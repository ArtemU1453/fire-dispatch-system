"""Response schemas for the search API."""

from __future__ import annotations

from uuid import UUID

from app.models.enums import ResourceCategory
from app.schemas.common import SchemaBase


class RefLabel(SchemaBase):
    """A lightweight reference (id + code/name) to a related catalog row."""

    id: UUID
    code: str | None = None
    name: str | None = None


class ResourceTypeRef(RefLabel):
    category: ResourceCategory | None = None


class ResourceSearchItem(SchemaBase):
    """A single resource in a search result (universal across resource kinds)."""

    id: UUID
    code: str
    name: str
    is_active: bool
    latitude: float | None = None
    longitude: float | None = None
    distance_meters: float | None = None
    resource_type: ResourceTypeRef | None = None
    organization: RefLabel | None = None
    availability_status: RefLabel | None = None
    # Which specialization (if any) this resource carries.
    specialization: str | None = None


class GeoPointOut(SchemaBase):
    latitude: float
    longitude: float


class SearchResponse(SchemaBase):
    """A page of search results with pagination metadata."""

    total: int
    limit: int
    offset: int
    count: int
    reference_point: GeoPointOut | None = None
    from_cache: bool = False
    items: list[ResourceSearchItem]
