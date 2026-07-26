"""Call queue management.

The queue holds calls that are waiting to be handled by a dispatcher. It tracks
**priority**, arrival time, the assigned dispatcher / workstation and a status,
and computes the current **wait time**. The design supports several dispatcher
workstations pulling from one shared queue.

This is a thin, persistence-backed manager: it mutates :class:`CallQueueEntry`
rows on the session (the owning service controls the transaction).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from app.calls.models.entities import Call, CallQueueEntry
from app.calls.models.enums import CallPriority, CallQueueStatus


def _now() -> datetime:
    return datetime.now(tz=UTC)


def wait_seconds(entry: CallQueueEntry, *, at: datetime | None = None) -> int:
    """Seconds the entry has been (or was) waiting before assignment."""
    end = entry.assigned_at or entry.removed_at or at or _now()
    return max(0, int((end - entry.enqueued_at).total_seconds()))


class CallQueueManager:
    """Creates and transitions queue entries for calls."""

    def enqueue(
        self, call: Call, *, priority: CallPriority | None = None
    ) -> CallQueueEntry:
        """Place a call in the queue (idempotent — reuses an open entry)."""
        entry = call.queue_entry
        if entry is not None and not entry.is_deleted:
            if priority is not None:
                entry.priority = priority
            return entry
        entry = CallQueueEntry(
            priority=priority or call.priority,
            status=CallQueueStatus.WAITING,
            enqueued_at=_now(),
        )
        call.queue_entry = entry
        return entry

    def assign(
        self,
        entry: CallQueueEntry,
        *,
        dispatcher_user_id: UUID | None = None,
        dispatcher_name: str | None = None,
        workstation: str | None = None,
    ) -> CallQueueEntry:
        entry.status = CallQueueStatus.ASSIGNED
        entry.assigned_at = _now()
        entry.dispatcher_user_id = dispatcher_user_id
        entry.dispatcher_name = dispatcher_name
        entry.workstation = workstation
        return entry

    def mark_in_progress(self, entry: CallQueueEntry) -> CallQueueEntry:
        entry.status = CallQueueStatus.IN_PROGRESS
        if entry.assigned_at is None:
            entry.assigned_at = _now()
        return entry

    def remove(
        self, entry: CallQueueEntry, *, abandoned: bool = False
    ) -> CallQueueEntry:
        entry.status = (
            CallQueueStatus.ABANDONED if abandoned else CallQueueStatus.DONE
        )
        entry.removed_at = _now()
        return entry
