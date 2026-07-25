"""Cache abstraction for geocoding results.

``GeoCache`` is an async key/value interface with TTL. Services depend on it, so
the in-memory implementation used now can be swapped for a Redis-backed one later
without touching service code (Dependency Inversion). The interface is
intentionally minimal and async so a Redis client drops in unchanged.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class GeoCache(ABC):
    """Async key/value cache with per-entry TTL."""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Return the cached value for ``key`` or ``None`` if absent/expired."""

    @abstractmethod
    async def set(self, key: str, value: Any, *, ttl: int | None = None) -> None:
        """Store ``value`` under ``key`` with an optional TTL (seconds)."""

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Remove ``key`` if present."""

    async def aclose(self) -> None:
        """Release resources (connections). Default no-op."""
        return None


class NullCache(GeoCache):
    """A cache that stores nothing — disables caching without branching."""

    async def get(self, key: str) -> Any | None:
        return None

    async def set(self, key: str, value: Any, *, ttl: int | None = None) -> None:
        return None

    async def delete(self, key: str) -> None:
        return None
