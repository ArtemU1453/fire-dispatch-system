"""Request schemas for the search API."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from app.models.enums import ResourceCategory
from app.schemas.common import SchemaBase
from app.search.criteria import SortDirection, SortField


class PaginationRequest(SchemaBase):
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class SortItem(SchemaBase):
    field: SortField
    direction: SortDirection = SortDirection.ASC


class FilterRequest(SchemaBase):
    """All resource filters — every field optional and freely combinable."""

    ids: list[UUID] = Field(default_factory=list)
    resource_type_ids: list[UUID] = Field(default_factory=list)
    categories: list[ResourceCategory] = Field(
        default_factory=list, description="Resource groups (ResourceType categories)."
    )
    organization_ids: list[UUID] = Field(default_factory=list)
    availability_status_ids: list[UUID] = Field(default_factory=list)
    capability_ids: list[UUID] = Field(default_factory=list)
    capability_match_all: bool = False
    station_ids: list[UUID] = Field(default_factory=list)
    vehicle_type_ids: list[UUID] = Field(default_factory=list)
    equipment_type_ids: list[UUID] = Field(default_factory=list)
    is_active: bool | None = None
    operational: bool | None = None
    deployable: bool | None = None
    name_contains: str | None = None
    code: str | None = None
    address_contains: str | None = None


class SpatialRequest(SchemaBase):
    """Optional spatial narrowing / reference."""

    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    radius_meters: float | None = Field(default=None, gt=0, le=1_000_000)
    polygon_wkt: str | None = None
    area_id: UUID | None = None
    bbox: tuple[float, float, float, float] | None = Field(
        default=None, description="(min_lon, min_lat, max_lon, max_lat)"
    )
    # If given (and no explicit coordinates), the address is geocoded to a point.
    address: str | None = None


class SearchRequest(SchemaBase):
    """Full combinable search: filters + spatial + sort + pagination."""

    filters: FilterRequest = Field(default_factory=FilterRequest)
    spatial: SpatialRequest = Field(default_factory=SpatialRequest)
    sort: list[SortItem] = Field(default_factory=list)
    pagination: PaginationRequest = Field(default_factory=PaginationRequest)


class NearestRequest(SchemaBase):
    """Nearest resources to a point (or geocoded address)."""

    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    address: str | None = None
    limit: int = Field(default=10, ge=1, le=500)
    filters: FilterRequest = Field(default_factory=FilterRequest)


class RadiusRequest(SchemaBase):
    """Resources within a radius of a point (or geocoded address)."""

    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    address: str | None = None
    radius_meters: float = Field(gt=0, le=1_000_000)
    pagination: PaginationRequest = Field(default_factory=PaginationRequest)
    filters: FilterRequest = Field(default_factory=FilterRequest)
