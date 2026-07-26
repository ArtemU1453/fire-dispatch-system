"""A small in-process TTL cache for analytics results (stage §10).

Aggregated KPI / statistics / trend results are cached briefly so repeated
dashboard reads don't re-run every aggregate query. Backend-agnostic and
dependency-free; a Redis-backed cache can replace it behind the same interface.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


class TTLCache:
    def __init__(self, ttl_seconds: float = 30.0) -> None:
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[float, object]] = {}
        self._lock = threading.Lock()

    def get(self, key: str):
        with self._lock:
            item = self._store.get(key)
            if item is None:
                return None
            expires, value = item
            if expires < time.monotonic():
                self._store.pop(key, None)
                return None
            return value

    def set(self, key: str, value: object) -> None:
        with self._lock:
            self._store[key] = (time.monotonic() + self._ttl, value)

    async def get_or_compute(
        self, key: str, compute: Callable[[], Awaitable[T]]
    ) -> T:
        cached = self.get(key)
        if cached is not None:
            return cached
        value = await compute()
        self.set(key, value)
        return value

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


# Process-wide analytics cache (short TTL — analytics is not real-time).
analytics_cache = TTLCache(ttl_seconds=30.0)
