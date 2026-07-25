"""Mapping between request/ORM and search primitives.

- ``build_filters`` turns a :class:`FilterRequest` into composable filters.
- ``to_item`` turns a scored ORM resource into a response item using only
  eager-loaded relationships (no lazy loads → no N+1).
"""

from __future__ import annotations

import hashlib

from app.models.resource import Resource
from app.search.algorithms.selection import ScoredResource
from app.search.filters import (
    AddressFilter,
    AvailabilityStatusFilter,
    CapabilityFilter,
    EquipmentTypeFilter,
    IdFilter,
    OrganizationFilter,
    ResourceFilter,
    ResourceGroupFilter,
    ResourceTypeFilter,
    StationFilter,
    TextFilter,
    VehicleTypeFilter,
    WorkingStatusFilter,
)
from app.search.schemas.requests import FilterRequest, SearchRequest
from app.search.schemas.responses import (
    RefLabel,
    ResourceSearchItem,
    ResourceTypeRef,
)


def build_filters(req: FilterRequest) -> list[ResourceFilter]:
    """Build the active filter list from a request (empty ones are dropped)."""
    candidates: list[ResourceFilter] = [
        IdFilter(req.ids),
        ResourceTypeFilter(req.resource_type_ids),
        ResourceGroupFilter(req.categories),
        OrganizationFilter(req.organization_ids),
        AvailabilityStatusFilter(req.availability_status_ids),
        CapabilityFilter(req.capability_ids, match_all=req.capability_match_all),
        StationFilter(req.station_ids),
        VehicleTypeFilter(req.vehicle_type_ids),
        EquipmentTypeFilter(req.equipment_type_ids),
        WorkingStatusFilter(
            is_active=req.is_active,
            operational=req.operational,
            deployable=req.deployable,
        ),
        TextFilter(name_contains=req.name_contains, code=req.code),
        AddressFilter(req.address_contains),
    ]
    return [f for f in candidates if f.is_active()]


def _specialization(resource: Resource) -> str | None:
    if resource.vehicle is not None:
        return "vehicle"
    if resource.station is not None:
        return "station"
    if resource.personnel is not None:
        return "personnel"
    if resource.equipment is not None:
        return "equipment"
    return None


def to_item(candidate: ScoredResource) -> ResourceSearchItem:
    r = candidate.resource
    rt = r.resource_type
    org = r.organization
    status = r.availability_status
    return ResourceSearchItem(
        id=r.id,
        code=r.code,
        name=r.name,
        is_active=r.is_active,
        latitude=r.latitude,
        longitude=r.longitude,
        distance_meters=candidate.distance_meters,
        resource_type=(
            ResourceTypeRef(id=rt.id, code=rt.code, name=rt.name, category=rt.category)
            if rt is not None
            else None
        ),
        organization=(
            RefLabel(id=org.id, code=org.code, name=org.name)
            if org is not None
            else None
        ),
        availability_status=(
            RefLabel(id=status.id, code=status.code, name=status.name)
            if status is not None
            else None
        ),
        specialization=_specialization(r),
    )


def cache_key(request: SearchRequest, *, reference: tuple | None) -> str:
    """Stable cache key for a search request (+ resolved reference point)."""
    raw = request.model_dump_json() + f"|ref={reference}"
    return "search:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()
