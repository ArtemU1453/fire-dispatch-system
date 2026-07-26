"""Incident technical log recorder (distinct from the timeline/history)."""

from __future__ import annotations

from typing import Any

from app.incidents.models.entities import Incident, IncidentLog
from app.incidents.utils.actor import Actor


class IncidentLogger:
    """Records technical/system log entries on an incident."""

    def log(
        self,
        incident: Incident,
        action: str,
        *,
        message: str | None = None,
        level: str = "info",
        actor: Actor | None = None,
        meta: dict[str, Any] | None = None,
    ) -> IncidentLog:
        entry = IncidentLog(
            action=action,
            message=message,
            level=level,
            actor_user_id=actor.user_id if actor else None,
            meta=meta,
        )
        incident.logs.append(entry)
        return entry
