"""Incident repository — eager-loading reads and lifecycle-aware listings."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.incidents.models.entities import Incident
from app.incidents.models.enums import IncidentStatus
from app.incidents.validators.state_machine import (
    ACTIVE_STATUSES,
    CLOSED_STATUSES,
)
from app.repositories.base import SqlAlchemyRepository


def _full_load_options() -> list:
    return [
        selectinload(Incident.locations),
        selectinload(Incident.participants),
        selectinload(Incident.comments),
        selectinload(Incident.attachments),
        selectinload(Incident.timeline),
        selectinload(Incident.history),
        selectinload(Incident.recommendations),
        selectinload(Incident.dispatches),
        selectinload(Incident.logs),
    ]


class IncidentRepository(SqlAlchemyRepository[Incident]):
    model = Incident

    async def get_full(self, incident_id: UUID) -> Incident | None:
        stmt = (
            select(Incident)
            .where(Incident.id == incident_id, Incident.is_deleted.is_(False))
            .options(*_full_load_options())
        )
        return (await self._session.execute(stmt)).scalars().first()

    async def get_by_number(self, number: str) -> Incident | None:
        stmt = (
            select(Incident)
            .where(Incident.number == number, Incident.is_deleted.is_(False))
            .options(*_full_load_options())
        )
        return (await self._session.execute(stmt)).scalars().first()

    async def list_incidents(
        self,
        *,
        statuses: Sequence[IncidentStatus] | None = None,
        active: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Incident]:
        stmt = select(Incident).where(Incident.is_deleted.is_(False))
        if active is True:
            stmt = stmt.where(Incident.status.in_(tuple(ACTIVE_STATUSES)))
        elif active is False:
            stmt = stmt.where(Incident.status.in_(tuple(CLOSED_STATUSES)))
        if statuses:
            stmt = stmt.where(Incident.status.in_(tuple(statuses)))
        stmt = (
            stmt.order_by(Incident.created_at.desc())
            .limit(limit)
            .offset(offset)
            .options(*_full_load_options())
        )
        return (await self._session.execute(stmt)).scalars().all()

    async def next_number(self) -> str:
        """A unique, human-readable incident number: ``INC-YYYYMMDD-XXXXXX``."""
        today = datetime.now(tz=UTC).strftime("%Y%m%d")
        return f"INC-{today}-{uuid4().hex[:6].upper()}"
