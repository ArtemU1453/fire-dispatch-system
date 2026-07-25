"""Geocoding cache (Redis-ready abstraction, in-memory default)."""

from app.config import Settings, get_settings
from app.gis.cache.base import GeoCache, NullCache
from app.gis.cache.memory import InMemoryGeoCache


def create_cache(settings: Settings | None = None) -> GeoCache:
    """Instantiate the configured :class:`GeoCache`.

    ``memory`` → process-local TTL cache; ``none`` → disabled. A Redis backend
    can be added here (guided by ``GIS_REDIS_URL``) without changing callers.
    """
    settings = settings or get_settings()
    if settings.GIS_CACHE_BACKEND == "memory":
        return InMemoryGeoCache(
            default_ttl=settings.GIS_CACHE_TTL_SECONDS,
            max_entries=settings.GIS_CACHE_MAX_ENTRIES,
        )
    return NullCache()


__all__ = ["GeoCache", "NullCache", "InMemoryGeoCache", "create_cache"]
