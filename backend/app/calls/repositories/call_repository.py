"""Call repository — eager-loading reads, queue and history queries (no N+1)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import case, select
from sqlalchemy.orm import selectinload

from app.calls.models.entities import (
    Call,
    CallHistory,
    CallQueueEntry,
)
from app.calls.models.enums import CallPriority, CallQueueStatus, CallStatus
from app.calls.validators.state_machine import ACTIVE_STATUSES, CLOSED_STATUSES
from app.repositories.base import SqlAlchemyRepository

# Queue statuses that still occupy the queue (a call waiting to be handled).
OPEN_QUEUE_STATUSES: tuple[CallQueueStatus, ...] = (
    CallQueueStatus.WAITING,
    CallQueueStatus.ASSIGNED,
    CallQueueStatus.IN_PROGRESS,
)

# Higher rank = more urgent (used to order the queue; enum labels don't sort).
_PRIORITY_RANK = {
    CallPriority.CRITICAL: 4,
    CallPriority.HIGH: 3,
    CallPriority.NORMAL: 2,
    CallPriority.LOW: 1,
}


def _priority_order():
    return case(_PRIORITY_RANK, value=CallQueueEntry.priority, else_=0)


def _full_load_options() -> list:
    return [
        selectinload(Call.queue_entry),
        selectinload(Call.history),
        selectinload(Call.participants),
        selectinload(Call.recordings),
        selectinload(Call.transcripts),
        selectinload(Call.links),
        selectinload(Call.call_metadata),
    ]


class CallRepository(SqlAlchemyRepository[Call]):
    model = Call

    async def get_full(self, call_id: UUID) -> Call | None:
        stmt = (
            select(Call)
            .where(Call.id == call_id, Call.is_deleted.is_(False))
            .options(*_full_load_options())
        )
        return (await self._session.execute(stmt)).scalars().first()

    async def get_by_number(self, number: str) -> Call | None:
        stmt = (
            select(Call)
            .where(Call.number == number, Call.is_deleted.is_(False))
            .options(*_full_load_options())
        )
        return (await self._session.execute(stmt)).scalars().first()

    async def list_calls(
        self,
        *,
        statuses: Sequence[CallStatus] | None = None,
        active: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Call]:
        stmt = select(Call).where(Call.is_deleted.is_(False))
        if active is True:
            stmt = stmt.where(Call.status.in_(tuple(ACTIVE_STATUSES)))
        elif active is False:
            stmt = stmt.where(Call.status.in_(tuple(CLOSED_STATUSES)))
        if statuses:
            stmt = stmt.where(Call.status.in_(tuple(statuses)))
        stmt = (
            stmt.order_by(Call.created_at.desc())
            .limit(limit)
            .offset(offset)
            .options(*_full_load_options())
        )
        return (await self._session.execute(stmt)).scalars().all()

    async def queue(
        self, *, limit: int = 100, offset: int = 0
    ) -> Sequence[CallQueueEntry]:
        """The open queue, most urgent first (priority, then arrival time)."""
        stmt = (
            select(CallQueueEntry)
            .where(
                CallQueueEntry.is_deleted.is_(False),
                CallQueueEntry.status.in_(OPEN_QUEUE_STATUSES),
            )
            .order_by(
                _priority_order().desc(),
                CallQueueEntry.enqueued_at.asc(),
            )
            .limit(limit)
            .offset(offset)
            .options(selectinload(CallQueueEntry.call))
        )
        return (await self._session.execute(stmt)).scalars().all()

    async def history(
        self,
        *,
        call_id: UUID | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> Sequence[CallHistory]:
        """Call history — for one call (``call_id``) or globally, newest first."""
        stmt = select(CallHistory)
        if call_id is not None:
            stmt = stmt.where(CallHistory.call_id == call_id)
        stmt = (
            stmt.order_by(CallHistory.occurred_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return (await self._session.execute(stmt)).scalars().all()

    async def next_number(self) -> str:
        """A unique, human-readable call number: ``CALL-YYYYMMDD-XXXXXX``."""
        today = datetime.now(tz=UTC).strftime("%Y%m%d")
        return f"CALL-{today}-{uuid4().hex[:6].upper()}"
