"""GIS dependency providers (Dependency Injection wiring).

Endpoints declare the services they need; these factories assemble them from the
request-scoped session plus the app-wide provider and cache (created once in the
application lifespan). Nothing in the API layer constructs a provider or cache
directly.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.api.deps import SessionDep, SettingsDep
from app.gis.cache.base import GeoCache
from app.gis.providers.base import GeoProvider
from app.gis.services.geocoding import GeocodingService
from app.gis.services.normalization import NormalizationService
from app.gis.services.spatial import SpatialService


def get_geo_provider(request: Request) -> GeoProvider:
    """Return the process-wide geocoding provider from app state."""
    return request.app.state.geo_provider


def get_geo_cache(request: Request) -> GeoCache:
    """Return the process-wide geocoding cache from app state."""
    return request.app.state.geo_cache


def get_normalization_service() -> NormalizationService:
    return NormalizationService()


GeoProviderDep = Annotated[GeoProvider, Depends(get_geo_provider)]
GeoCacheDep = Annotated[GeoCache, Depends(get_geo_cache)]
NormalizationDep = Annotated[NormalizationService, Depends(get_normalization_service)]


def get_geocoding_service(
    provider: GeoProviderDep,
    cache: GeoCacheDep,
    normalization: NormalizationDep,
    settings: SettingsDep,
) -> GeocodingService:
    return GeocodingService(
        provider=provider,
        cache=cache,
        normalization=normalization,
        settings=settings,
    )


def get_spatial_service(session: SessionDep) -> SpatialService:
    return SpatialService(session)


GeocodingServiceDep = Annotated[GeocodingService, Depends(get_geocoding_service)]
SpatialServiceDep = Annotated[SpatialService, Depends(get_spatial_service)]
