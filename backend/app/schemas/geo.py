"""Schemas for geospatial entities.

Geometry is exposed to clients as GeoJSON-friendly scalars (``latitude`` /
``longitude`` for points) and, for areas, an optional WKT string. The raw PostGIS
``geom`` column is derived server-side and never sent over the wire.
"""

from __future__ import annotations

from uuid import UUID

from app.schemas.common import ResponseBase, SchemaBase

# ----------------------------------------------------------- administrative --


class AdministrativeAreaCreate(SchemaBase):
    code: str
    name: str
    level: int = 0
    parent_id: UUID | None = None
    boundary_wkt: str | None = None


class AdministrativeAreaUpdate(SchemaBase):
    code: str | None = None
    name: str | None = None
    level: int | None = None
    parent_id: UUID | None = None
    boundary_wkt: str | None = None


class AdministrativeAreaResponse(ResponseBase):
    code: str
    name: str
    level: int
    parent_id: UUID | None = None


# ------------------------------------------------------------------ location --


class LocationCreate(SchemaBase):
    name: str | None = None
    address: str | None = None
    administrative_area_id: UUID | None = None
    latitude: float | None = None
    longitude: float | None = None


class LocationUpdate(SchemaBase):
    name: str | None = None
    address: str | None = None
    administrative_area_id: UUID | None = None
    latitude: float | None = None
    longitude: float | None = None


class LocationResponse(ResponseBase):
    name: str | None = None
    address: str | None = None
    administrative_area_id: UUID | None = None
    latitude: float | None = None
    longitude: float | None = None


# ------------------------------------------------------------- coverage area --


class CoverageAreaCreate(SchemaBase):
    name: str
    resource_id: UUID | None = None
    administrative_area_id: UUID | None = None
    priority: int = 0
    area_wkt: str | None = None


class CoverageAreaUpdate(SchemaBase):
    name: str | None = None
    resource_id: UUID | None = None
    administrative_area_id: UUID | None = None
    priority: int | None = None
    area_wkt: str | None = None


class CoverageAreaResponse(ResponseBase):
    name: str
    resource_id: UUID | None = None
    administrative_area_id: UUID | None = None
    priority: int


class CoverageAreaIncidentTypeCreate(SchemaBase):
    coverage_area_id: UUID
    incident_type_id: UUID
    priority: int = 0


class CoverageAreaIncidentTypeUpdate(SchemaBase):
    priority: int | None = None


class CoverageAreaIncidentTypeResponse(ResponseBase):
    coverage_area_id: UUID
    incident_type_id: UUID
    priority: int
