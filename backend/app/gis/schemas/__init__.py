"""GIS Pydantic schemas."""

from app.gis.schemas.geocoding import (
    AddressComponentsSchema,
    CoordinatesResponse,
    GeocodeResponse,
    GeocodeResultSchema,
    NormalizeResponse,
    ReverseGeocodeResponse,
    ValidateResponse,
)
from app.gis.schemas.models import (
    AddressCreate,
    AddressResponse,
    AddressUpdate,
    BuildingCreate,
    BuildingResponse,
    BuildingUpdate,
    CoordinateCreate,
    CoordinateResponse,
    CoordinateUpdate,
    DistrictCreate,
    DistrictResponse,
    DistrictUpdate,
    GeocodingLogResponse,
    RegionCreate,
    RegionResponse,
    RegionUpdate,
    SettlementCreate,
    SettlementResponse,
    SettlementUpdate,
    StreetCreate,
    StreetResponse,
    StreetUpdate,
)
from app.gis.schemas.spatial import (
    DistanceResponse,
    SpatialObject,
    SpatialSearchResponse,
)

__all__ = [
    # geocoding API
    "GeocodeResultSchema",
    "GeocodeResponse",
    "AddressComponentsSchema",
    "ReverseGeocodeResponse",
    "NormalizeResponse",
    "ValidateResponse",
    "CoordinatesResponse",
    # spatial API
    "DistanceResponse",
    "SpatialObject",
    "SpatialSearchResponse",
    # model CRUD
    "RegionCreate", "RegionUpdate", "RegionResponse",
    "DistrictCreate", "DistrictUpdate", "DistrictResponse",
    "SettlementCreate", "SettlementUpdate", "SettlementResponse",
    "StreetCreate", "StreetUpdate", "StreetResponse",
    "BuildingCreate", "BuildingUpdate", "BuildingResponse",
    "CoordinateCreate", "CoordinateUpdate", "CoordinateResponse",
    "AddressCreate", "AddressUpdate", "AddressResponse",
    "GeocodingLogResponse",
]
