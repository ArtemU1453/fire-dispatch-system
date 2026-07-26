"""Commander service — command-staff views (Stage 19).

Server-side aggregation for the Commander app: dashboard, incidents, resource
load, map data and critical notifications, plus notes / comments / decision
confirmations. All computed here; the app only renders the result.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from app.mobile.providers.base import MobileDataProvider
from app.mobile.providers.types import (
    CriticalNotification,
    MobileIncident,
    OperationalSummary,
    ResourceLoad,
)

_CRITICAL_PRIORITIES = {"high", "critical"}


@dataclass
class Note:
    id: str
    author: str
    text: str
    created_at: str
    incident_id: str | None = None
    kind: str = "note"          # note | comment | confirmation


@dataclass
class CommanderDashboard:
    summary: OperationalSummary
    active_incidents: list[MobileIncident]
    resource_load: list[ResourceLoad]
    critical: list[CriticalNotification]


class CommanderService:
    def __init__(self, provider: MobileDataProvider) -> None:
        self._provider = provider
        self._notes: list[Note] = []

    # ------------------------------------------------------------- views
    def dashboard(self) -> CommanderDashboard:
        incidents = self._provider.list_incidents(active_only=True)
        return CommanderDashboard(
            summary=self._provider.operational_summary(),
            active_incidents=incidents,
            resource_load=self._provider.list_resources(),
            critical=self._critical_from(incidents),
        )

    def incidents(self, *, active_only: bool = True) -> list[MobileIncident]:
        return self._provider.list_incidents(active_only=active_only)

    def resources(self) -> list[ResourceLoad]:
        return self._provider.list_resources()

    def map_data(self) -> dict:
        incidents = [
            i for i in self._provider.list_incidents(active_only=True)
            if i.lat is not None and i.lon is not None
        ]
        units = [
            r for r in self._provider.list_resources()
            if r.lat is not None and r.lon is not None
        ]
        return {"incidents": incidents, "units": units}

    def critical_notifications(self) -> list[CriticalNotification]:
        return self._critical_from(self._provider.list_incidents(active_only=True))

    def _critical_from(
        self, incidents: list[MobileIncident]
    ) -> list[CriticalNotification]:
        out: list[CriticalNotification] = []
        for inc in incidents:
            if inc.priority in _CRITICAL_PRIORITIES:
                out.append(
                    CriticalNotification(
                        id=f"crit-{inc.id}",
                        type="incident",
                        message=f"{inc.category}: {inc.address}",
                        created_at=inc.created_at,
                        incident_id=inc.id,
                        severity="critical" if inc.priority == "critical" else "high",
                    )
                )
        return out

    # ------------------------------------------------------------- notes
    def add_note(
        self, *, author: str, text: str, incident_id: str | None = None,
        kind: str = "note",
    ) -> Note:
        note = Note(
            id=uuid4().hex,
            author=author,
            text=text.strip(),
            created_at=datetime.now(tz=UTC).isoformat(),
            incident_id=incident_id,
            kind=kind,
        )
        self._notes.append(note)
        return note

    def list_notes(self, *, incident_id: str | None = None) -> list[Note]:
        if incident_id is None:
            return list(self._notes)
        return [n for n in self._notes if n.incident_id == incident_id]
