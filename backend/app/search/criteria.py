"""Search criteria value objects.

``SearchCriteria`` is the single, provider-agnostic description of a search that
the :class:`SearchEngine` consumes. It carries the composable filters, an optional
spatial constraint, sorting and pagination — nothing about *how* the query runs.
Keeping it a plain dataclass makes the engine easy to test and lets the next
stage (automatic unit selection) build criteria programmatically.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from app.search.filters.base import ResourceFilter


class SortField(str, Enum):
    """Fields a search result can be ordered by."""

    DISTANCE = "distance"        # requires a reference point
    NAME = "name"
    ORGANIZATION = "organization"
    STATUS = "status"
    TYPE = "type"
    PRIORITY = "priority"        # availability status sort order
    READINESS = "readiness"      # deployable-for-dispatch first


class SortDirection(str, Enum):
    ASC = "asc"
    DESC = "desc"


@dataclass(slots=True)
class SortSpec:
    field: SortField
    direction: SortDirection = SortDirection.ASC


@dataclass(slots=True)
class GeoPoint:
    latitude: float
    longitude: float


@dataclass(slots=True)
class SpatialConstraint:
    """Optional spatial narrowing / reference for a search.

    - ``point`` + ``radius_meters`` → within-radius (and enables distance sort).
    - ``point`` alone → nearest (KNN) ordering / distance annotation.
    - ``polygon_wkt`` → within a WKT polygon.
    - ``area_id`` → within a Stage-2 administrative area boundary.
    - ``bbox`` → within a bounding box (min_lon, min_lat, max_lon, max_lat).
    """

    point: GeoPoint | None = None
    radius_meters: float | None = None
    polygon_wkt: str | None = None
    area_id: UUID | None = None
    bbox: tuple[float, float, float, float] | None = None


@dataclass(slots=True)
class Pagination:
    limit: int = 50
    offset: int = 0


@dataclass(slots=True)
class SearchCriteria:
    """A complete, executable description of a resource search."""

    filters: list[ResourceFilter] = field(default_factory=list)
    spatial: SpatialConstraint = field(default_factory=SpatialConstraint)
    sort: list[SortSpec] = field(default_factory=list)
    pagination: Pagination = field(default_factory=Pagination)

    @property
    def reference_point(self) -> GeoPoint | None:
        return self.spatial.point
