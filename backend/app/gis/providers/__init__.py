"""Geocoding providers (pluggable backends behind :class:`GeoProvider`)."""

from app.gis.providers.arcgis import ArcGISProvider
from app.gis.providers.base import (
    AddressComponents,
    GeoAccuracy,
    GeocodeQuery,
    GeocodeResult,
    GeoProvider,
    GeoProviderError,
    ReverseResult,
)
from app.gis.providers.factory import PROVIDER_REGISTRY, create_provider
from app.gis.providers.fake import FakeGeoProvider
from app.gis.providers.nominatim import NominatimProvider
from app.gis.providers.pelias import PeliasProvider
from app.gis.providers.photon import PhotonProvider

__all__ = [
    "GeoProvider",
    "GeoProviderError",
    "GeoAccuracy",
    "GeocodeQuery",
    "GeocodeResult",
    "ReverseResult",
    "AddressComponents",
    "NominatimProvider",
    "PhotonProvider",
    "PeliasProvider",
    "ArcGISProvider",
    "FakeGeoProvider",
    "create_provider",
    "PROVIDER_REGISTRY",
]
