"""Search dependency providers (Dependency Injection wiring)."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.api.deps import SessionDep
from app.gis.cache.base import GeoCache
from app.gis.deps import GeocodingServiceDep
from app.search.services import SearchService


def get_search_cache(request: Request) -> GeoCache:
    """Return the process-wide search cache from app state."""
    return request.app.state.search_cache


SearchCacheDep = Annotated[GeoCache, Depends(get_search_cache)]


def get_search_service(
    session: SessionDep,
    geocoding: GeocodingServiceDep,
    cache: SearchCacheDep,
) -> SearchService:
    return SearchService(session, geocoding=geocoding, cache=cache)


SearchServiceDep = Annotated[SearchService, Depends(get_search_service)]
