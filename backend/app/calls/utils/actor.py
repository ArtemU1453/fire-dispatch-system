"""The actor performing a call action (dispatcher / system / integration)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class Actor:
    """Who performed a change. No auth backend yet — name is free-form.

    ``source`` is stored on history entries as a free-form label (``dispatcher``
    / ``system`` / ``integration``) so a future telephony or AI integration can
    attribute automatic changes.
    """

    user_id: UUID | None = None
    name: str | None = None
    source: str = "dispatcher"

    @classmethod
    def system(cls) -> Actor:
        return cls(name="system", source="system")
