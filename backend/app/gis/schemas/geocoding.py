"""Request/response schemas for the geocoding API."""

from __future__ import annotations

from app.gis.providers.base import GeoAccuracy
from app.schemas.common import SchemaBase


class GeocodeResultSchema(SchemaBase):
    formatted_address: str
    normalized_address: str | None = None
    latitude: float
    longitude: float
    accuracy: GeoAccuracy
    source: str


class GeocodeResponse(SchemaBase):
    query: str
    normalized_address: str
    provider: str
    from_cache: bool
    success: bool
    error: str | None = None
    count: int
    results: list[GeocodeResultSchema]


class AddressComponentsSchema(SchemaBase):
    country: str | None = None
    country_code: str | None = None
    region: str | None = None
    district: str | None = None
    settlement: str | None = None
    street: str | None = None
    house_number: str | None = None
    postal_code: str | None = None
    formatted_address: str | None = None


class ReverseGeocodeResponse(SchemaBase):
    latitude: float
    longitude: float
    provider: str
    from_cache: bool
    success: bool
    error: str | None = None
    accuracy: GeoAccuracy | None = None
    source: str | None = None
    address: AddressComponentsSchema | None = None


class NormalizeResponse(SchemaBase):
    raw: str
    normalized: str
    canonical: str


class ValidateResponse(SchemaBase):
    query: str
    normalized_address: str
    is_valid: bool
    best_match: GeocodeResultSchema | None = None


class CoordinatesResponse(SchemaBase):
    query: str
    normalized_address: str
    found: bool
    latitude: float | None = None
    longitude: float | None = None
    accuracy: GeoAccuracy | None = None
    source: str | None = None
