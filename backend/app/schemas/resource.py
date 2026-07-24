"""Schemas for the core :class:`Resource` and :class:`ResourceCapability`."""

from __future__ import annotations

from uuid import UUID

from app.schemas.common import ResponseBase, SchemaBase


class ResourceBase(SchemaBase):
    code: str
    name: str
    description: str | None = None
    is_active: bool = True
    resource_type_id: UUID
    organization_id: UUID
    availability_status_id: UUID | None = None
    location_id: UUID | None = None
    home_station_id: UUID | None = None
    latitude: float | None = None
    longitude: float | None = None


class ResourceCreate(ResourceBase):
    pass


class ResourceUpdate(SchemaBase):
    code: str | None = None
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None
    resource_type_id: UUID | None = None
    organization_id: UUID | None = None
    availability_status_id: UUID | None = None
    location_id: UUID | None = None
    home_station_id: UUID | None = None
    latitude: float | None = None
    longitude: float | None = None


class ResourceResponse(ResponseBase):
    code: str
    name: str
    description: str | None = None
    is_active: bool
    resource_type_id: UUID
    organization_id: UUID
    availability_status_id: UUID | None = None
    location_id: UUID | None = None
    home_station_id: UUID | None = None
    latitude: float | None = None
    longitude: float | None = None


class ResourceCapabilityCreate(SchemaBase):
    resource_id: UUID
    capability_id: UUID
    quantity: int = 1


class ResourceCapabilityUpdate(SchemaBase):
    quantity: int | None = None


class ResourceCapabilityResponse(ResponseBase):
    resource_id: UUID
    capability_id: UUID
    quantity: int
