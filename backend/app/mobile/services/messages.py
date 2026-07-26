"""Short service messages between the field and command (Stage 19).

In-memory store of brief operational messages (BFF state, no production DB).
Sending a message can trigger a push notification to the recipient.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


@dataclass
class ServiceMessage:
    id: str
    from_user: str
    text: str
    created_at: str
    unit_id: str | None = None
    incident_id: str | None = None


@dataclass
class MessageStore:
    _messages: list[ServiceMessage] = field(default_factory=list)

    def add(
        self,
        *,
        from_user: str,
        text: str,
        unit_id: str | None = None,
        incident_id: str | None = None,
    ) -> ServiceMessage:
        msg = ServiceMessage(
            id=uuid4().hex,
            from_user=from_user,
            text=text.strip(),
            created_at=datetime.now(tz=UTC).isoformat(),
            unit_id=unit_id,
            incident_id=incident_id,
        )
        self._messages.append(msg)
        return msg

    def list(
        self, *, unit_id: str | None = None, incident_id: str | None = None
    ) -> list[ServiceMessage]:
        items = self._messages
        if unit_id is not None:
            items = [m for m in items if m.unit_id == unit_id]
        if incident_id is not None:
            items = [m for m in items if m.incident_id == incident_id]
        return list(items)
