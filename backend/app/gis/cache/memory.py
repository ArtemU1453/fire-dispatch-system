"""In-memory TTL cache implementation of :class:`GeoCache`.

Suitable for a single process / development. Bounded by ``max_entries`` with
simple FIFO eviction and lazy expiry. For multi-process deployments swap in a
Redis-backed :class:`GeoCache` (the interface is identical).
"""

from __future__ import annotations

import time
from collections import OrderedDict
from typing import Any


class InMemoryGeoCache:
    """Process-local key/value cache with TTL and a size bound."""

    def __init__(self, *, default_ttl: int = 86400, max_entries: int = 10000) -> None:
        self._default_ttl = default_ttl
        self._max_entries = max_entries
        # key -> (expires_at_epoch, value)
        self._store: OrderedDict[str, tuple[float, Any]] = OrderedDict()

    async def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if expires_at < time.monotonic():
            self._store.pop(key, None)
            return None
        self._store.move_to_end(key)
        return value

    async def set(self, key: str, value: Any, *, ttl: int | None = None) -> None:
        expires_at = time.monotonic() + (ttl if ttl is not None else self._default_ttl)
        self._store[key] = (expires_at, value)
        self._store.move_to_end(key)
        while len(self._store) > self._max_entries:
            self._store.popitem(last=False)  # FIFO eviction

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def aclose(self) -> None:
        self._store.clear()
