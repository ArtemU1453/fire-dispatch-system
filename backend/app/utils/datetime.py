"""Small, dependency-free datetime helpers.

Centralising these keeps time handling consistent (always timezone-aware, UTC)
across the code base.
"""

from __future__ import annotations

from datetime import UTC, datetime


def utcnow() -> datetime:
    """Return the current time as a timezone-aware UTC ``datetime``."""
    return datetime.now(tz=UTC)
