"""Hermetic unit tests for the search engine (no database)."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy.dialects import postgresql

from app.models.enums import ResourceCategory
from app.search.algorithms.selection import IdentitySelection, ScoredResource
from app.search.criteria import (
    GeoPoint,
    SearchCriteria,
    SortField,
    SortSpec,
    SpatialConstraint,
)
from app.search.engine import SearchEngine
from app.search.filters import CapabilityFilter, ResourceGroupFilter
from app.search.schemas.requests import FilterRequest, SearchRequest, SpatialRequest
from app.search.utils.mapping import build_filters, cache_key


def _compile(stmt) -> str:
    return str(stmt.compile(dialect=postgresql.dialect()))


def test_build_filters_drops_empty() -> None:
    req = FilterRequest(categories=[ResourceCategory.VEHICLE], name_contains="ac")
    filters = build_filters(req)
    # Only the two active filters are produced.
    assert len(filters) == 2


def test_build_filters_empty_request_is_empty() -> None:
    assert build_filters(FilterRequest()) == []


def test_engine_emits_expected_sql() -> None:
    criteria = SearchCriteria(
        filters=[
            ResourceGroupFilter([ResourceCategory.VEHICLE]),
            CapabilityFilter([uuid4()]),
        ],
        spatial=SpatialConstraint(
            point=GeoPoint(55.75, 37.62), radius_meters=1000
        ),
        sort=[SortSpec(SortField.DISTANCE)],
    )
    built = SearchEngine().build(criteria)
    page_sql = _compile(built.page)
    assert "ST_DWithin" in page_sql
    assert "is_deleted" in page_sql
    assert "EXISTS" in page_sql.upper()
    assert "count" in _compile(built.count).lower()


def test_engine_no_point_has_no_distance() -> None:
    built = SearchEngine().build(SearchCriteria())
    assert built.has_distance is False
    assert "ST_Distance" not in _compile(built.page)


def test_bbox_sql_uses_envelope() -> None:
    criteria = SearchCriteria(
        spatial=SpatialConstraint(bbox=(37.5, 55.7, 37.7, 55.8))
    )
    assert "ST_MakeEnvelope" in _compile(SearchEngine().build(criteria).page)


def test_cache_key_is_deterministic_and_sensitive() -> None:
    a = SearchRequest(spatial=SpatialRequest(latitude=1.0, longitude=2.0))
    b = SearchRequest(spatial=SpatialRequest(latitude=1.0, longitude=2.0))
    c = SearchRequest(spatial=SpatialRequest(latitude=9.0, longitude=2.0))
    assert cache_key(a, reference=(1.0, 2.0)) == cache_key(b, reference=(1.0, 2.0))
    assert cache_key(a, reference=(1.0, 2.0)) != cache_key(c, reference=(9.0, 2.0))


def test_identity_selection_passthrough() -> None:
    candidates = [
        ScoredResource(resource=object(), distance_meters=float(i))  # type: ignore[arg-type]
        for i in range(3)
    ]
    assert IdentitySelection().apply(candidates) == candidates
