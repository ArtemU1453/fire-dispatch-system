"""Integration tests for ResourceManagementService (require PostgreSQL).

These verify the behaviour the DoD cares about most: that a status change on a
unit / vehicle updates the underlying Stage-2 ``resources.availability_status``
the Dispatch Engine reads (without touching any Dispatch code), and that the
history table is append-only.
"""

from __future__ import annotations

from uuid import UUID

import pytest

from app.models.resource import Resource
from app.resources.models.enums import AssignmentStatus, ResourceEventType
from app.resources.services.resource_management_service import (
    ResourceManagementService,
)

from .conftest import ResourceSeed

pytestmark = pytest.mark.asyncio


async def _status_id(service: ResourceManagementService, code: str) -> UUID:
    status = await service._repo.status_by_code(code)
    assert status is not None
    return status.id


async def test_update_unit_status_propagates_to_vehicle_resource(
    pg_factory, seed: ResourceSeed
) -> None:
    """The Dispatch Engine reads resources.availability_status — it must move."""
    async with pg_factory() as s:
        service = ResourceManagementService(s)
        on_scene = await _status_id(service, "on_scene")
        await service.update_unit_status(
            UUID(seed.unit_id), "on_scene", actor_name="tester"
        )
        await s.commit()

    async with pg_factory() as s:
        unit = await ResourceManagementService(s).get_unit(UUID(seed.unit_id))
        assert unit.availability_status.code == "on_scene"
        # The vehicle resource the Dispatch Engine reads followed the unit.
        vehicle = await s.get(Resource, UUID(seed.vehicle_resource_id))
        assert vehicle.availability_status_id == on_scene


async def test_update_vehicle_status_writes_history_and_status(
    pg_factory, seed: ResourceSeed
) -> None:
    async with pg_factory() as s:
        service = ResourceManagementService(s)
        await service.update_resource_status(
            UUID(seed.vehicle_resource_id),
            "maintenance",
            event=ResourceEventType.VEHICLE_STATUS_CHANGED,
            actor_name="tester",
        )
        await s.commit()

    async with pg_factory() as s:
        service = ResourceManagementService(s)
        vehicle = await s.get(Resource, UUID(seed.vehicle_resource_id))
        status = await service._repo.status_by_code("maintenance")
        assert vehicle.availability_status_id == status.id
        history = await service.history(resource_id=UUID(seed.vehicle_resource_id))
        assert any(
            h.event_type is ResourceEventType.VEHICLE_STATUS_CHANGED
            and h.to_value == "maintenance"
            for h in history
        )


async def test_bulk_update_status(pg_factory, seed: ResourceSeed) -> None:
    async with pg_factory() as s:
        service = ResourceManagementService(s)
        count = await service.bulk_update_status(
            [UUID(seed.vehicle_resource_id), UUID(seed.personnel_resource_id)],
            "reserve",
            actor_name="tester",
        )
        await s.commit()
    assert count == 2

    async with pg_factory() as s:
        service = ResourceManagementService(s)
        reserve = await service._repo.status_by_code("reserve")
        for rid in (seed.vehicle_resource_id, seed.personnel_resource_id):
            res = await s.get(Resource, UUID(rid))
            assert res.availability_status_id == reserve.id


async def test_assign_crew_and_change_composition(
    pg_factory, seed: ResourceSeed
) -> None:
    async with pg_factory() as s:
        service = ResourceManagementService(s)
        # Detach the seeded crew from its (absent) unit, then attach it.
        unit = await service.assign_crew(
            UUID(seed.unit_id), UUID(seed.crew_id), actor_name="tester"
        )
        assert len([c for c in unit.crews if not c.is_deleted]) == 1
        # Remove the only member.
        crew = await service.change_crew_composition(
            UUID(seed.crew_id),
            remove=[UUID(seed.personnel_resource_id)],
            actor_name="tester",
        )
        assert [m for m in crew.members if not m.is_deleted] == []
        await s.commit()

    async with pg_factory() as s:
        service = ResourceManagementService(s)
        crew = await service._repo.crew(UUID(seed.crew_id))
        active = [m for m in crew.members if not m.is_deleted]
        assert active == []


async def test_assign_and_return_incident(
    pg_factory, seed: ResourceSeed
) -> None:
    async with pg_factory() as s:
        service = ResourceManagementService(s)
        unit = await service.assign_to_incident(
            UUID(seed.unit_id), UUID(seed.incident_id), actor_name="tester"
        )
        active = [
            a
            for a in unit.assignments
            if a.status is AssignmentStatus.ACTIVE and not a.is_deleted
        ]
        assert len(active) == 1
        await s.commit()

    async with pg_factory() as s:
        service = ResourceManagementService(s)
        unit = await service.return_from_incident(
            UUID(seed.unit_id), actor_name="tester"
        )
        active = [
            a
            for a in unit.assignments
            if a.status is AssignmentStatus.ACTIVE and not a.is_deleted
        ]
        assert active == []
        await s.commit()

    async with pg_factory() as s:
        service = ResourceManagementService(s)
        got = await service.get_unit(UUID(seed.unit_id))
        released = [
            a for a in got.assignments if a.status is AssignmentStatus.RELEASED
        ]
        assert len(released) == 1


async def test_history_is_append_only(pg_factory, seed: ResourceSeed) -> None:
    async with pg_factory() as s:
        service = ResourceManagementService(s)
        await service.update_unit_status(UUID(seed.unit_id), "enroute")
        await service.update_unit_status(UUID(seed.unit_id), "on_scene")
        await service.update_unit_status(UUID(seed.unit_id), "returning")
        await s.commit()

    async with pg_factory() as s:
        service = ResourceManagementService(s)
        history = await service.history(unit_id=UUID(seed.unit_id))
        values = [h.to_value for h in history]
        # All three transitions preserved (append-only, never overwritten).
        assert {"enroute", "on_scene", "returning"} <= set(values)
        assert len(values) >= 3


async def test_check_availability_and_location(
    pg_factory, seed: ResourceSeed
) -> None:
    async with pg_factory() as s:
        service = ResourceManagementService(s)
        assert await service.check_availability(
            UUID(seed.vehicle_resource_id)
        ) is True
        await service.update_resource_status(
            UUID(seed.vehicle_resource_id),
            "repair",
            event=ResourceEventType.VEHICLE_STATUS_CHANGED,
        )
        await s.commit()

    async with pg_factory() as s:
        service = ResourceManagementService(s)
        assert await service.check_availability(
            UUID(seed.vehicle_resource_id)
        ) is False
        loc = await service.get_location(UUID(seed.vehicle_resource_id))
        assert loc is not None
        assert round(loc.latitude, 2) == 55.75
        assert round(loc.longitude, 2) == 37.62


async def test_status_overview_counts_resources(
    pg_factory, seed: ResourceSeed
) -> None:
    async with pg_factory() as s:
        service = ResourceManagementService(s)
        overview = await service.status_overview()
        by_code = {status.code: count for status, count in overview}
        # All 9 seeded statuses appear; the two seeded resources start "free".
        assert len(by_code) >= 9
        assert by_code.get("free", 0) >= 2
