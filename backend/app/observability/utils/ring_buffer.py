"""A tiny thread-safe ring buffer for recent logs / traces / alerts.

Keeps the last *N* items in memory — backend-agnostic and dependency-free, so it
can later be replaced by (or fed into) Prometheus / OpenTelemetry / ELK without
changing callers.
"""

from __future__ import annotations

import threading
from collections import deque
from collections.abc import Iterable
from typing import Generic, TypeVar

T = TypeVar("T")


class RingBuffer(Generic[T]):
    def __init__(self, maxlen: int = 1000) -> None:
        self._items: deque[T] = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def append(self, item: T) -> None:
        with self._lock:
            self._items.append(item)

    def snapshot(self, *, limit: int | None = None) -> list[T]:
        """Most-recent-first list of items (optionally limited)."""
        with self._lock:
            items = list(self._items)
        items.reverse()
        return items[:limit] if limit is not None else items

    def extend(self, items: Iterable[T]) -> None:
        with self._lock:
            self._items.extend(items)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._items)
