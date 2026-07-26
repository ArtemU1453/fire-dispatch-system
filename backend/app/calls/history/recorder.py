"""Append-only history recorder for calls.

Every meaningful change to a call (status change, queueing, dispatcher
assignment, incident creation / linking, provider action) is captured as a
:class:`~app.calls.models.entities.CallHistory` row — with the time, actor,
source, old → new status and the related incident. History is **never deleted**.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.calls.models.entities import Call, CallHistory
from app.calls.models.enums import CallEventType, CallStatus


class CallHistoryRecorder:
    """Creates append-only history entries on a call."""

    def record(
        self,
        call: Call,
        event_type: CallEventType,
        *,
        from_status: CallStatus | None = None,
        to_status: CallStatus | None = None,
        actor_name: str | None = None,
        actor_user_id: UUID | None = None,
        source: str = "dispatcher",
        incident_id: UUID | None = None,
        detail: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> CallHistory:
        entry = CallHistory(
            event_type=event_type,
            from_status=from_status,
            to_status=to_status,
            changed_by_name=actor_name,
            changed_by_user_id=actor_user_id,
            source=source,
            incident_id=incident_id,
            detail=detail,
            meta=meta,
        )
        call.history.append(entry)
        return entry
