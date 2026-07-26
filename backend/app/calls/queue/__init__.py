"""Call queue management."""

from __future__ import annotations

from app.calls.queue.manager import CallQueueManager, wait_seconds

__all__ = ["CallQueueManager", "wait_seconds"]
