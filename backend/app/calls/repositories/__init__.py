"""Call-management repositories."""

from __future__ import annotations

from app.calls.repositories.call_repository import (
    OPEN_QUEUE_STATUSES,
    CallRepository,
)

__all__ = ["OPEN_QUEUE_STATUSES", "CallRepository"]
