"""The actor performing an action (dispatcher / system / integration)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.incidents.models.enums import ChangeSource


@dataclass(slots=True)
class Actor:
    """Who performed a change. No auth backend yet — name is free-form."""

    user_id: UUID | None = None
    name: str | None = None
    source: ChangeSource = ChangeSource.DISPATCHER

    @classmethod
    def system(cls) -> Actor:
        return cls(name="system", source=ChangeSource.SYSTEM)
