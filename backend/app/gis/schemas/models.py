"""Pydantic Create/Update/Response schemas for the GIS models.

Reuses the Stage-2 ``SchemaBase`` / ``ResponseBase`` (identity + audit fields).
Geometry is exposed as ``latitude``/``longitude`` scalars or WKT strings; the raw
PostGIS ``geom`` is derived server-side and never serialized.
"""

from __future__ import annotations

from uuid import UUID

from app.schemas.common import ResponseBase, SchemaBase

# ------------------------------------------------------------------- region --


class RegionCreate(SchemaBase):
    name: str
    code: str | None = None
    administrative_area_id: UUID | None = None
    boundary_wkt: str | None = None


class RegionUpdate(SchemaBase):
    name: str | None = None
    code: str | None = None
    administrative_area_id: UUID | None = None
    boundary_wkt: str | None = None


class RegionResponse(ResponseBase):
    name: str
    code: str | None = None
    administrative_area_id: UUID | None = None


# ----------------------------------------------------------------- district --


class DistrictCreate(SchemaBase):
    name: str
    region_id: UUID
    boundary_wkt: str | None = None


class DistrictUpdate(SchemaBase):
    name: str | None = None
    region_id: UUID | None = None
    boundary_wkt: str | None = None


class DistrictResponse(ResponseBase):
    name: str
    region_id: UUID


# --------------------------------------------------------------- settlement --


class SettlementCreate(SchemaBase):
    name: str
    settlement_type: str | None = None
    district_id: UUID | None = None
    region_id: UUID | None = None
    latitude: float | None = None
    longitude: float | None = None


class SettlementUpdate(SchemaBase):
    name: str | None = None
    settlement_type: str | None = None
    district_id: UUID | None = None
    region_id: UUID | None = None
    latitude: float | None = None
    longitude: float | None = None


class SettlementResponse(ResponseBase):
    name: str
    settlement_type: str | None = None
    district_id: UUID | None = None
    region_id: UUID | None = None
    latitude: float | None = None
    longitude: float | None = None


# ------------------------------------------------------------------- street --


class StreetCreate(SchemaBase):
    name: str
    street_type: str | None = None
    settlement_id: UUID


class StreetUpdate(SchemaBase):
    name: str | None = None
    street_type: str | None = None
    settlement_id: UUID | None = None


class StreetResponse(ResponseBase):
    name: str
    street_type: str | None = None
    settlement_id: UUID


# ----------------------------------------------------------------- building --


class BuildingCreate(SchemaBase):
    house_number: str
    block: str | None = None
    building: str | None = None
    postal_code: str | None = None
    street_id: UUID | None = None
    latitude: float | None = None
    longitude: float | None = None


class BuildingUpdate(SchemaBase):
    house_number: str | None = None
    block: str | None = None
    building: str | None = None
    postal_code: str | None = None
    street_id: UUID | None = None
    latitude: float | None = None
    longitude: float | None = None


class BuildingResponse(ResponseBase):
    house_number: str
    block: str | None = None
    building: str | None = None
    postal_code: str | None = None
    street_id: UUID | None = None
    latitude: float | None = None
    longitude: float | None = None


# --------------------------------------------------------------- coordinate --


class CoordinateCreate(SchemaBase):
    latitude: float
    longitude: float
    srid: int = 4326
    accuracy: str | None = None
    source: str | None = None


class CoordinateUpdate(SchemaBase):
    latitude: float | None = None
    longitude: float | None = None
    accuracy: str | None = None
    source: str | None = None


class CoordinateResponse(ResponseBase):
    latitude: float | None = None
    longitude: float | None = None
    srid: int
    accuracy: str | None = None
    source: str | None = None


# ------------------------------------------------------------------ address --


class AddressCreate(SchemaBase):
    raw_address: str
    normalized_address: str | None = None
    formatted_address: str | None = None
    country: str | None = None
    country_code: str | None = None
    postal_code: str | None = None
    house_number: str | None = None
    accuracy: str | None = None
    source: str | None = None
    region_id: UUID | None = None
    district_id: UUID | None = None
    settlement_id: UUID | None = None
    street_id: UUID | None = None
    building_id: UUID | None = None
    coordinate_id: UUID | None = None
    latitude: float | None = None
    longitude: float | None = None


class AddressUpdate(SchemaBase):
    normalized_address: str | None = None
    formatted_address: str | None = None
    country: str | None = None
    country_code: str | None = None
    postal_code: str | None = None
    house_number: str | None = None
    accuracy: str | None = None
    is_validated: bool | None = None
    region_id: UUID | None = None
    district_id: UUID | None = None
    settlement_id: UUID | None = None
    street_id: UUID | None = None
    building_id: UUID | None = None
    coordinate_id: UUID | None = None
    latitude: float | None = None
    longitude: float | None = None


class AddressResponse(ResponseBase):
    raw_address: str
    normalized_address: str | None = None
    formatted_address: str | None = None
    country: str | None = None
    country_code: str | None = None
    postal_code: str | None = None
    house_number: str | None = None
    accuracy: str | None = None
    source: str | None = None
    is_validated: bool
    region_id: UUID | None = None
    district_id: UUID | None = None
    settlement_id: UUID | None = None
    street_id: UUID | None = None
    building_id: UUID | None = None
    coordinate_id: UUID | None = None
    latitude: float | None = None
    longitude: float | None = None


# ------------------------------------------------------------ geocoding log --


class GeocodingLogResponse(ResponseBase):
    operation: str
    provider: str
    query: str
    success: bool
    result_count: int
    response_time_ms: float | None = None
    source: str | None = None
    error: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    from_cache: bool
