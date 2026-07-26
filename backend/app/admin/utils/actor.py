"""The administrator performing an action."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class Actor:
    """Who performed an administrative change (no auth backend yet)."""

    user_id: UUID | None = None
    name: str | None = None
    ip_address: str | None = None
