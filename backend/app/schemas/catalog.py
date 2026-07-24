"""Schemas for catalog (lookup) entities.

A small set of ``Catalog*`` bases capture the shared ``code`` / ``name`` /
``description`` shape so each concrete catalog schema only declares its extras.
"""

from __future__ import annotations

from uuid import UUID

from app.models.enums import ResourceCategory
from app.schemas.common import ResponseBase, SchemaBase

# --------------------------------------------------------------------- bases --


class CatalogCreateBase(SchemaBase):
    code: str
    name: str
    description: str | None = None


class CatalogUpdateBase(SchemaBase):
    code: str | None = None
    name: str | None = None
    description: str | None = None


class CatalogResponseBase(ResponseBase):
    code: str
    name: str
    description: str | None = None


# ------------------------------------------------------------- resource type --


class ResourceTypeCreate(CatalogCreateBase):
    category: ResourceCategory


class ResourceTypeUpdate(CatalogUpdateBase):
    category: ResourceCategory | None = None


class ResourceTypeResponse(CatalogResponseBase):
    category: ResourceCategory


# -------------------------------------------------------------- vehicle type --


class VehicleTypeCreate(CatalogCreateBase):
    pass


class VehicleTypeUpdate(CatalogUpdateBase):
    pass


class VehicleTypeResponse(CatalogResponseBase):
    pass


# ------------------------------------------------------------ personnel role --


class PersonnelRoleCreate(CatalogCreateBase):
    pass


class PersonnelRoleUpdate(CatalogUpdateBase):
    pass


class PersonnelRoleResponse(CatalogResponseBase):
    pass


# ------------------------------------------------------------ equipment type --


class EquipmentTypeCreate(CatalogCreateBase):
    pass


class EquipmentTypeUpdate(CatalogUpdateBase):
    pass


class EquipmentTypeResponse(CatalogResponseBase):
    pass


# ------------------------------------------------------- availability status --


class AvailabilityStatusCreate(CatalogCreateBase):
    is_operational: bool = True
    is_available_for_dispatch: bool = False
    color: str | None = None
    sort_order: int = 0


class AvailabilityStatusUpdate(CatalogUpdateBase):
    is_operational: bool | None = None
    is_available_for_dispatch: bool | None = None
    color: str | None = None
    sort_order: int | None = None


class AvailabilityStatusResponse(CatalogResponseBase):
    is_operational: bool
    is_available_for_dispatch: bool
    color: str | None = None
    sort_order: int


# ----------------------------------------------------------------- capability --


class CapabilityCreate(CatalogCreateBase):
    pass


class CapabilityUpdate(CatalogUpdateBase):
    pass


class CapabilityResponse(CatalogResponseBase):
    pass


# -------------------------------------------------------------- incident type --


class IncidentTypeCreate(CatalogCreateBase):
    parent_id: UUID | None = None


class IncidentTypeUpdate(CatalogUpdateBase):
    parent_id: UUID | None = None


class IncidentTypeResponse(CatalogResponseBase):
    parent_id: UUID | None = None


class IncidentTypeCapabilityCreate(SchemaBase):
    incident_type_id: UUID
    capability_id: UUID
    min_quantity: int = 1


class IncidentTypeCapabilityUpdate(SchemaBase):
    min_quantity: int | None = None


class IncidentTypeCapabilityResponse(ResponseBase):
    incident_type_id: UUID
    capability_id: UUID
    min_quantity: int
