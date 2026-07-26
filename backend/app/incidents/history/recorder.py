"""History recorder — field-level audit of every card change.

Records **who** changed **what**, **when**, the **old** and **new** value and the
**source** of the change — exactly the audit the stage requires. Values are
stored as strings for a uniform, queryable trail.
"""

from __future__ import annotations

from typing import Any

from app.incidents.models.entities import Incident, IncidentHistory
from app.incidents.utils.actor import Actor


def _as_text(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "value"):  # enum
        return str(value.value)
    return str(value)


class HistoryRecorder:
    """Records field changes on an incident."""

    def record(
        self,
        incident: Incident,
        field: str,
        old_value: Any,
        new_value: Any,
        *,
        actor: Actor | None = None,
        note: str | None = None,
    ) -> IncidentHistory:
        entry = IncidentHistory(
            field=field,
            old_value=_as_text(old_value),
            new_value=_as_text(new_value),
            change_source=actor.source if actor else None,
            changed_by_user_id=actor.user_id if actor else None,
            changed_by_name=actor.name if actor else None,
            note=note,
        )
        incident.history.append(entry)
        return entry

    def record_changes(
        self,
        incident: Incident,
        changes: dict[str, tuple[Any, Any]],
        *,
        actor: Actor | None = None,
    ) -> list[IncidentHistory]:
        """Record several ``field -> (old, new)`` changes (skips no-ops)."""
        entries: list[IncidentHistory] = []
        for field, (old, new) in changes.items():
            if old != new:
                entries.append(
                    self.record(incident, field, old, new, actor=actor)
                )
        return entries
