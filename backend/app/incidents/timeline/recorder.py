"""Timeline recorder — appends chronology entries to an incident.

The timeline is the human-facing sequence of what happened to an incident
(created, address changed, recommendation requested, units assigned, status
changed, comment added, closed, …). Entries are appended through the incident's
loaded relationship so no lazy load fires under the async engine.
"""

from __future__ import annotations

from typing import Any

from app.incidents.models.entities import Incident, IncidentTimeline
from app.incidents.models.enums import TimelineEventType
from app.incidents.utils.actor import Actor


class TimelineRecorder:
    """Records timeline events on an incident."""

    def record(
        self,
        incident: Incident,
        event_type: TimelineEventType,
        title: str,
        *,
        detail: str | None = None,
        actor: Actor | None = None,
        meta: dict[str, Any] | None = None,
    ) -> IncidentTimeline:
        entry = IncidentTimeline(
            event_type=event_type,
            title=title,
            detail=detail,
            actor_user_id=actor.user_id if actor else None,
            actor_name=actor.name if actor else None,
            meta=meta,
        )
        incident.timeline.append(entry)
        return entry
