"""Request/response schemas for the spatial API."""

from __future__ import annotations

from uuid import UUID

from app.schemas.common import SchemaBase


class DistanceResponse(SchemaBase):
    distance_meters: float


class SpatialObject(SchemaBase):
    """A geom-bearing object returned by a spatial query (e.g. a resource).

    Deliberately minimal — identity and location only. Ranking/selection for
    dispatch is out of scope for this stage.
    """

    id: UUID
    code: str | None = None
    name: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class SpatialSearchResponse(SchemaBase):
    count: int
    items: list[SpatialObject]
