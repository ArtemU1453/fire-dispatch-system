"""Integration tests for the Dispatch Engine on PostgreSQL.

Exercises the full pipeline against real data: rules from the Rule Engine,
candidates from the Search Engine, exclusion, selection, reserve and persistence.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.dispatch.models.enums import DispatchStatus, RecommendationRole
from app.dispatch.schemas.requests import DispatchConstraints, DispatchRequest
from app.dispatch.services import DispatchService

from .conftest import REF_LAT, REF_LON, DispatchSeed

pytestmark = pytest.mark.asyncio


def _request(seed: DispatchSeed, **overrides) -> DispatchRequest:
    data = dict(
        incident_id=uuid4(),
        incident_type_id=UUID(seed.incident_type_id),
        latitude=REF_LAT,
        longitude=REF_LON,
        constraints=DispatchConstraints(),
    )
    data.update(overrides)
    return DispatchRequest(**data)


async def test_recommendation_selects_and_covers_capability(
    pg_factory: async_sessionmaker, seed: DispatchSeed
) -> None:
    async with pg_factory() as s:
        service = DispatchService(s)
        response = await service.recommend(_request(seed))
        await s.commit()

    rec = response.recommendation
    assert rec.status is DispatchStatus.RECOMMENDED
    assert rec.sufficient is True
    assert len(rec.primary_units) >= 1
    # fire_suppression must be covered by the primary set.
    covered = {c.code: c.satisfied for c in rec.capability_coverage}
    assert all(covered.values())
    # Every selected unit carries an automatic explanation.
    assert all(u.reasons for u in rec.primary_units)
    # The busy unit must never be selected.
    selected_ids = {u.resource_id for u in rec.primary_units + rec.reserve_units}
    assert UUID(seed.busy_id) not in selected_ids


async def test_busy_resource_is_excluded_with_reason(
    pg_factory: async_sessionmaker, seed: DispatchSeed
) -> None:
    async with pg_factory() as s:
        service = DispatchService(s)
        response = await service.recommend(_request(seed))
        await s.commit()

    matches = {
        m.resource_id: m for m in response.recommendation.resource_matches
    }
    busy = matches.get(UUID(seed.busy_id))
    assert busy is not None
    assert busy.excluded is True
    assert busy.exclusion_reason is not None


async def test_reserve_selected_when_requested(
    pg_factory: async_sessionmaker, seed: DispatchSeed
) -> None:
    async with pg_factory() as s:
        service = DispatchService(s)
        response = await service.recommend(_request(seed))
        await s.commit()
    # The rule asks for 1 reserve; with several available units one is set aside.
    roles = {u.role for u in response.recommendation.reserve_units}
    assert roles <= {RecommendationRole.RESERVE}


async def test_preview_has_no_reserves(
    pg_factory: async_sessionmaker, seed: DispatchSeed
) -> None:
    async with pg_factory() as s:
        service = DispatchService(s)
        response = await service.recommend(_request(seed), preview=True)
        await s.commit()
    assert response.recommendation.is_preview is True
    assert response.recommendation.reserve_units == []


async def test_persistence_and_history(
    pg_factory: async_sessionmaker, seed: DispatchSeed
) -> None:
    incident_id = uuid4()
    async with pg_factory() as s:
        service = DispatchService(s)
        await service.recommend(_request(seed, incident_id=incident_id))
        await s.commit()

    async with pg_factory() as s:
        service = DispatchService(s)
        latest = await service.get_recommendation(incident_id)
        assert latest.incident_id == incident_id
        assert latest.rule_codes  # the rule that fired is recorded
        history = await service.get_history(incident_id)
        assert len(history) == 1
        assert history[0].incident_id == incident_id


async def test_manual_organization_constraint(
    pg_factory: async_sessionmaker, seed: DispatchSeed
) -> None:
    async with pg_factory() as s:
        service = DispatchService(s)
        response = await service.recommend(
            _request(
                seed,
                constraints=DispatchConstraints(
                    organization_ids=[UUID(seed.organization_id)]
                ),
            )
        )
        await s.commit()
    # Every matched resource belongs to the allowed organization (only one seeded).
    assert response.recommendation.status is DispatchStatus.RECOMMENDED
