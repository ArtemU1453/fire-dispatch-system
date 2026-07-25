"""Concrete, composable resource filters.

All narrowings are expressed against the core ``Resource`` so the engine works
identically for any resource type (fire station, vehicle, hydrant, hospital,
police, …) — the type is just another filter.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import Select, and_, exists, func, select

from app.models.assets import Equipment, Vehicle
from app.models.catalog import AvailabilityStatus, ResourceType
from app.models.enums import ResourceCategory
from app.models.geo import Location
from app.models.resource import Resource, ResourceCapability
from app.search.filters.base import ResourceFilter


class ResourceTypeFilter(ResourceFilter):
    """Restrict to specific resource types (by ResourceType id)."""

    def __init__(self, type_ids: Sequence[UUID]) -> None:
        self._type_ids = list(type_ids)

    def is_active(self) -> bool:
        return bool(self._type_ids)

    def apply(self, stmt: Select) -> Select:
        if not self._type_ids:
            return stmt
        return stmt.where(Resource.resource_type_id.in_(self._type_ids))


class ResourceGroupFilter(ResourceFilter):
    """Restrict to resource-type *categories* (e.g. STATION, VEHICLE, FACILITY).

    A "resource group" is a family of resource types; matched via the type's
    ``category`` so no algorithm change is needed to search a new group.
    """

    def __init__(self, categories: Sequence[ResourceCategory]) -> None:
        self._categories = list(categories)

    def is_active(self) -> bool:
        return bool(self._categories)

    def apply(self, stmt: Select) -> Select:
        if not self._categories:
            return stmt
        return stmt.where(
            exists(
                select(ResourceType.id).where(
                    and_(
                        ResourceType.id == Resource.resource_type_id,
                        ResourceType.category.in_(self._categories),
                    )
                )
            )
        )


class OrganizationFilter(ResourceFilter):
    def __init__(self, organization_ids: Sequence[UUID]) -> None:
        self._ids = list(organization_ids)

    def is_active(self) -> bool:
        return bool(self._ids)

    def apply(self, stmt: Select) -> Select:
        if not self._ids:
            return stmt
        return stmt.where(Resource.organization_id.in_(self._ids))


class AvailabilityStatusFilter(ResourceFilter):
    def __init__(self, status_ids: Sequence[UUID]) -> None:
        self._ids = list(status_ids)

    def is_active(self) -> bool:
        return bool(self._ids)

    def apply(self, stmt: Select) -> Select:
        if not self._ids:
            return stmt
        return stmt.where(Resource.availability_status_id.in_(self._ids))


class WorkingStatusFilter(ResourceFilter):
    """Filter by operational readiness.

    ``is_active`` → the resource flag; ``operational`` / ``deployable`` →
    properties of the linked availability status.
    """

    def __init__(
        self,
        *,
        is_active: bool | None = None,
        operational: bool | None = None,
        deployable: bool | None = None,
    ) -> None:
        self._is_active = is_active
        self._operational = operational
        self._deployable = deployable

    def is_active(self) -> bool:
        values = (self._is_active, self._operational, self._deployable)
        return any(v is not None for v in values)

    def apply(self, stmt: Select) -> Select:
        if self._is_active is not None:
            stmt = stmt.where(Resource.is_active.is_(self._is_active))
        status_conditions = []
        if self._operational is not None:
            status_conditions.append(
                AvailabilityStatus.is_operational.is_(self._operational)
            )
        if self._deployable is not None:
            status_conditions.append(
                AvailabilityStatus.is_available_for_dispatch.is_(self._deployable)
            )
        if status_conditions:
            stmt = stmt.where(
                exists(
                    select(AvailabilityStatus.id).where(
                        and_(
                            AvailabilityStatus.id == Resource.availability_status_id,
                            *status_conditions,
                        )
                    )
                )
            )
        return stmt


class StationFilter(ResourceFilter):
    """Restrict to resources based at specific home stations."""

    def __init__(self, station_ids: Sequence[UUID]) -> None:
        self._ids = list(station_ids)

    def is_active(self) -> bool:
        return bool(self._ids)

    def apply(self, stmt: Select) -> Select:
        if not self._ids:
            return stmt
        return stmt.where(Resource.home_station_id.in_(self._ids))


class CapabilityFilter(ResourceFilter):
    """Restrict to resources providing given capabilities.

    ``match_all=False`` (default) → provides *any* of the capabilities;
    ``match_all=True`` → provides *all* of them.
    """

    def __init__(
        self, capability_ids: Sequence[UUID], *, match_all: bool = False
    ) -> None:
        self._ids = list(capability_ids)
        self._match_all = match_all

    def is_active(self) -> bool:
        return bool(self._ids)

    def apply(self, stmt: Select) -> Select:
        if not self._ids:
            return stmt
        if self._match_all:
            count = (
                select(func.count(func.distinct(ResourceCapability.capability_id)))
                .where(
                    and_(
                        ResourceCapability.resource_id == Resource.id,
                        ResourceCapability.capability_id.in_(self._ids),
                        ResourceCapability.is_deleted.is_(False),
                    )
                )
                .scalar_subquery()
            )
            return stmt.where(count == len(set(self._ids)))
        return stmt.where(
            exists(
                select(ResourceCapability.id).where(
                    and_(
                        ResourceCapability.resource_id == Resource.id,
                        ResourceCapability.capability_id.in_(self._ids),
                        ResourceCapability.is_deleted.is_(False),
                    )
                )
            )
        )


class VehicleTypeFilter(ResourceFilter):
    def __init__(self, vehicle_type_ids: Sequence[UUID]) -> None:
        self._ids = list(vehicle_type_ids)

    def is_active(self) -> bool:
        return bool(self._ids)

    def apply(self, stmt: Select) -> Select:
        if not self._ids:
            return stmt
        return stmt.where(
            exists(
                select(Vehicle.id).where(
                    and_(
                        Vehicle.resource_id == Resource.id,
                        Vehicle.vehicle_type_id.in_(self._ids),
                        Vehicle.is_deleted.is_(False),
                    )
                )
            )
        )


class EquipmentTypeFilter(ResourceFilter):
    def __init__(self, equipment_type_ids: Sequence[UUID]) -> None:
        self._ids = list(equipment_type_ids)

    def is_active(self) -> bool:
        return bool(self._ids)

    def apply(self, stmt: Select) -> Select:
        if not self._ids:
            return stmt
        return stmt.where(
            exists(
                select(Equipment.id).where(
                    and_(
                        Equipment.resource_id == Resource.id,
                        Equipment.equipment_type_id.in_(self._ids),
                        Equipment.is_deleted.is_(False),
                    )
                )
            )
        )


class IdFilter(ResourceFilter):
    def __init__(self, ids: Sequence[UUID]) -> None:
        self._ids = list(ids)

    def is_active(self) -> bool:
        return bool(self._ids)

    def apply(self, stmt: Select) -> Select:
        if not self._ids:
            return stmt
        return stmt.where(Resource.id.in_(self._ids))


class TextFilter(ResourceFilter):
    """Case-insensitive match on name (partial), or exact code."""

    def __init__(
        self, *, name_contains: str | None = None, code: str | None = None
    ) -> None:
        self._name = name_contains
        self._code = code

    def is_active(self) -> bool:
        return bool(self._name or self._code)

    def apply(self, stmt: Select) -> Select:
        if self._name:
            stmt = stmt.where(Resource.name.ilike(f"%{self._name}%"))
        if self._code:
            stmt = stmt.where(Resource.code == self._code)
        return stmt


class AddressFilter(ResourceFilter):
    """Match resources whose registered location address contains the text."""

    def __init__(self, address_contains: str | None) -> None:
        self._address = address_contains

    def is_active(self) -> bool:
        return bool(self._address)

    def apply(self, stmt: Select) -> Select:
        if not self._address:
            return stmt
        return stmt.where(
            exists(
                select(Location.id).where(
                    and_(
                        Location.id == Resource.location_id,
                        Location.address.ilike(f"%{self._address}%"),
                    )
                )
            )
        )
