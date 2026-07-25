"""Behavioural tests for the SearchEngine against PostGIS (skip if no DB)."""

from __future__ import annotations

import pytest

from app.models.enums import ResourceCategory
from app.search.criteria import (
    GeoPoint,
    Pagination,
    SearchCriteria,
    SortDirection,
    SortField,
    SortSpec,
    SpatialConstraint,
)
from app.search.engine import SearchEngine
from app.search.filters import (
    CapabilityFilter,
    OrganizationFilter,
    ResourceGroupFilter,
    ResourceTypeFilter,
    TextFilter,
)
from app.search.repositories import SearchRepository

pytestmark = pytest.mark.asyncio

REF = GeoPoint(55.7539, 37.6208)


async def _run(session, criteria):
    return await SearchRepository(session).execute(SearchEngine().build(criteria))


async def test_radius_excludes_far_and_sorts_by_distance(session, seed) -> None:
    result = await _run(
        session,
        SearchCriteria(
            filters=[ResourceGroupFilter([ResourceCategory.VEHICLE])],
            spatial=SpatialConstraint(point=REF, radius_meters=5000),
            sort=[SortSpec(SortField.DISTANCE)],
        ),
    )
    names = [c.resource.name for c in result.candidates]
    assert names == ["NEAR", "MID"]  # FAR excluded, nearest first
    assert result.candidates[0].distance_meters < result.candidates[1].distance_meters


async def test_nearest_orders_all_by_distance(session, seed) -> None:
    result = await _run(
        session,
        SearchCriteria(
            filters=[ResourceGroupFilter([ResourceCategory.VEHICLE])],
            spatial=SpatialConstraint(point=REF),
            sort=[SortSpec(SortField.DISTANCE)],
        ),
    )
    assert [c.resource.name for c in result.candidates] == ["NEAR", "MID", "FAR"]


async def test_type_filter(session, seed) -> None:
    result = await _run(
        session, SearchCriteria(filters=[ResourceTypeFilter([seed.hydrant_type_id])])
    )
    assert {c.resource.name for c in result.candidates} == {"HYDRANT"}


async def test_category_group_filter(session, seed) -> None:
    result = await _run(
        session,
        SearchCriteria(filters=[ResourceGroupFilter([ResourceCategory.INFRASTRUCTURE])]),
    )
    assert {c.resource.name for c in result.candidates} == {"HYDRANT"}


async def test_capability_filter(session, seed) -> None:
    result = await _run(
        session, SearchCriteria(filters=[CapabilityFilter([seed.capability_id])])
    )
    assert {c.resource.name for c in result.candidates} == {"NEAR"}


async def test_organization_filter(session, seed) -> None:
    result = await _run(
        session, SearchCriteria(filters=[OrganizationFilter([seed.organization_id])])
    )
    assert result.total == 4  # all seeded resources share the org


async def test_text_filter_partial_name(session, seed) -> None:
    result = await _run(
        session, SearchCriteria(filters=[TextFilter(name_contains="EAR")])
    )
    assert {c.resource.name for c in result.candidates} == {"NEAR"}


async def test_sort_by_name_desc(session, seed) -> None:
    result = await _run(
        session, SearchCriteria(sort=[SortSpec(SortField.NAME, SortDirection.DESC)])
    )
    names = [c.resource.name for c in result.candidates]
    assert names == sorted(names, reverse=True)


async def test_pagination_limits_and_reports_total(session, seed) -> None:
    result = await _run(
        session,
        SearchCriteria(
            sort=[SortSpec(SortField.NAME)], pagination=Pagination(limit=2, offset=0)
        ),
    )
    assert result.total == 4
    assert len(result.candidates) == 2


async def test_combined_filters(session, seed) -> None:
    result = await _run(
        session,
        SearchCriteria(
            filters=[
                ResourceGroupFilter([ResourceCategory.VEHICLE]),
                CapabilityFilter([seed.capability_id]),
                OrganizationFilter([seed.organization_id]),
            ],
            spatial=SpatialConstraint(point=REF, radius_meters=5000),
            sort=[SortSpec(SortField.DISTANCE)],
        ),
    )
    assert [c.resource.name for c in result.candidates] == ["NEAR"]
