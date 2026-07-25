"""Integration tests for IncidentService on PostgreSQL."""

from __future__ import annotations

from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.exceptions import ValidationError
from app.incidents.models.enums import (
    IncidentPriority,
    IncidentStatus,
    TimelineEventType,
)
from app.incidents.schemas.incident import (
    AssignUnitInput,
    AssignUnitsRequest,
    CommentCreate,
    IncidentCreate,
    IncidentUpdate,
    StatusChangeRequest,
)
from app.incidents.services import IncidentService

from .conftest import REF_LAT, REF_LON, IncidentSeed

pytestmark = pytest.mark.asyncio


def _create(seed: IncidentSeed) -> IncidentCreate:
    return IncidentCreate(
        incident_type_id=UUID(seed.incident_type_id),
        address="ул. Тверская, 1",
        latitude=REF_LAT,
        longitude=REF_LON,
        actor_name="Диспетчер",
    )


async def test_create_records_timeline_and_location(
    pg_factory: async_sessionmaker, seed: IncidentSeed
) -> None:
    async with pg_factory() as s:
        incident = await IncidentService(s).create(_create(seed))
        await s.commit()
    assert incident.number.startswith("INC-")
    assert incident.status is IncidentStatus.CREATED
    assert any(e.event_type is TimelineEventType.CREATED for e in incident.timeline)
    assert len(incident.locations) == 1 and incident.locations[0].is_primary


async def test_update_records_field_history(
    pg_factory: async_sessionmaker, seed: IncidentSeed
) -> None:
    async with pg_factory() as s:
        service = IncidentService(s)
        incident = await service.create(_create(seed))
        await s.commit()
        updated = await service.update(
            incident.id,
            IncidentUpdate(priority=IncidentPriority.CRITICAL, title="Крупный пожар"),
        )
        await s.commit()
    fields = {h.field for h in updated.history}
    assert "priority" in fields and "title" in fields
    priority_change = next(h for h in updated.history if h.field == "priority")
    assert priority_change.old_value == "normal"
    assert priority_change.new_value == "critical"
    assert any(
        e.event_type is TimelineEventType.PRIORITY_CHANGED for e in updated.timeline
    )


async def test_valid_status_progression(
    pg_factory: async_sessionmaker, seed: IncidentSeed
) -> None:
    async with pg_factory() as s:
        service = IncidentService(s)
        incident = await service.create(_create(seed))
        await s.commit()
        await service.change_status(
            incident.id, StatusChangeRequest(status=IncidentStatus.CHECKING)
        )
        result = await service.change_status(
            incident.id, StatusChangeRequest(status=IncidentStatus.CONFIRMED)
        )
        await s.commit()
    assert result.status is IncidentStatus.CONFIRMED
    assert result.confirmed_at is not None
    assert any(h.field == "status" for h in result.history)


async def test_invalid_status_transition_is_rejected(
    pg_factory: async_sessionmaker, seed: IncidentSeed
) -> None:
    async with pg_factory() as s:
        service = IncidentService(s)
        incident = await service.create(_create(seed))
        await s.commit()
        with pytest.raises(ValidationError):
            await service.change_status(
                incident.id, StatusChangeRequest(status=IncidentStatus.DISPATCHED)
            )


async def test_comment_and_assign_units(
    pg_factory: async_sessionmaker, seed: IncidentSeed
) -> None:
    async with pg_factory() as s:
        service = IncidentService(s)
        incident = await service.create(_create(seed))
        await s.commit()
        await service.add_comment(
            incident.id, CommentCreate(text="Уточнить адрес", author_name="Д")
        )
        assigned = await service.assign_units(
            incident.id,
            AssignUnitsRequest(
                units=[AssignUnitInput(resource_id=UUID(seed.resource_id))]
            ),
        )
        # A second assignment of the same unit is de-duplicated.
        assigned = await service.assign_units(
            incident.id,
            AssignUnitsRequest(
                units=[AssignUnitInput(resource_id=UUID(seed.resource_id))]
            ),
        )
        await s.commit()
    assert len(assigned.comments) == 1
    assert len(assigned.dispatches) == 1
    assert any(
        e.event_type is TimelineEventType.UNITS_ASSIGNED for e in assigned.timeline
    )


async def test_request_recommendation_links_dispatch(
    pg_factory: async_sessionmaker, seed: IncidentSeed
) -> None:
    async with pg_factory() as s:
        service = IncidentService(s)
        incident = await service.create(_create(seed))
        await s.commit()
        result = await service.request_recommendation(incident.id, actor_name="Д")
        await s.commit()
    assert len(result.recommendations) == 1
    assert result.recommendations[0].recommendation_id is not None
    assert any(
        e.event_type is TimelineEventType.RECOMMENDATION_REQUESTED
        for e in result.timeline
    )


async def test_active_and_archive_listing(
    pg_factory: async_sessionmaker, seed: IncidentSeed
) -> None:
    async with pg_factory() as s:
        service = IncidentService(s)
        active_inc = await service.create(_create(seed))
        closed_inc = await service.create(_create(seed))
        await s.commit()
        # Cancel one (a valid pre-dispatch transition) → it becomes closed.
        await service.change_status(
            closed_inc.id, StatusChangeRequest(status=IncidentStatus.CANCELLED)
        )
        await s.commit()

        active = await service.list_incidents(active=True)
        archived = await service.list_incidents(active=False)
    active_ids = {i.id for i in active}
    archived_ids = {i.id for i in archived}
    assert active_inc.id in active_ids
    assert closed_inc.id in archived_ids
