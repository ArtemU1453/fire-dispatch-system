"""Search result cache factory.

Reuses the Stage-3 Redis-ready ``GeoCache`` abstraction so search results are
cached with the same interface (in-memory now, Redis later). Search results are
short-lived (resource state changes), hence a small default TTL.
"""

from __future__ import annotations

from app.config import Settings, get_settings
from app.gis.cache.base import GeoCache, NullCache
from app.gis.cache.memory import InMemoryGeoCache


def create_search_cache(settings: Settings | None = None) -> GeoCache:
    """Instantiate the configured search cache."""
    settings = settings or get_settings()
    if settings.SEARCH_CACHE_BACKEND == "memory":
        return InMemoryGeoCache(
            default_ttl=settings.SEARCH_CACHE_TTL_SECONDS,
            max_entries=settings.SEARCH_CACHE_MAX_ENTRIES,
        )
    return NullCache()
