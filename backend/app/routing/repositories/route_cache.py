"""Route reuse cache (in-memory; Redis-ready abstraction).

Routes between the same two points don't change during a short window, so caching
avoids repeated provider calls. The :class:`RouteCache` interface keeps the store
swappable — an in-memory TTL/LRU cache is provided now; a Redis backend can be
added later without touching the services (no Redis at this stage).
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections import OrderedDict

from app.routing.models.domain import GeoPoint, Route, TravelProfile


def route_cache_key(
    origin: GeoPoint,
    destination: GeoPoint,
    profile: TravelProfile,
    *,
    precision: int = 5,
) -> str:
    """A stable key for an O→D pair (coordinates rounded to ~1 m)."""
    return (
        f"{profile.value}:"
        f"{round(origin.latitude, precision)},{round(origin.longitude, precision)}"
        f"->{round(destination.latitude, precision)},"
        f"{round(destination.longitude, precision)}"
    )


class RouteCache(ABC):
    """Abstract route cache."""

    @abstractmethod
    async def get(self, key: str) -> Route | None: ...

    @abstractmethod
    async def set(self, key: str, route: Route) -> None: ...

    async def aclose(self) -> None:
        return None


class NullRouteCache(RouteCache):
    """Disabled cache (always a miss)."""

    async def get(self, key: str) -> Route | None:
        return None

    async def set(self, key: str, route: Route) -> None:
        return None


class InMemoryRouteCache(RouteCache):
    """Process-local TTL + LRU cache."""

    def __init__(self, *, default_ttl: int = 120, max_entries: int = 2000) -> None:
        self._ttl = default_ttl
        self._max = max_entries
        self._store: OrderedDict[str, tuple[float, Route]] = OrderedDict()

    async def get(self, key: str) -> Route | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, route = entry
        if expires_at < time.monotonic():
            self._store.pop(key, None)
            return None
        self._store.move_to_end(key)
        return route

    async def set(self, key: str, route: Route) -> None:
        self._store[key] = (time.monotonic() + self._ttl, route)
        self._store.move_to_end(key)
        while len(self._store) > self._max:
            self._store.popitem(last=False)


def create_route_cache(
    *, backend: str = "memory", ttl_seconds: int = 120, max_entries: int = 2000
) -> RouteCache:
    """Build the configured route cache."""
    if backend == "memory":
        return InMemoryRouteCache(default_ttl=ttl_seconds, max_entries=max_entries)
    return NullRouteCache()
