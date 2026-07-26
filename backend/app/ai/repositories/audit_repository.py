"""Read access to the AI audit log."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.models.entities import AIAuditLog
from app.ai.models.enums import AIAuditCapability


class AIAuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_entries(
        self,
        *,
        capability: AIAuditCapability | None = None,
        provider: str | None = None,
        call_id: UUID | None = None,
        incident_id: UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[AIAuditLog]:
        stmt = select(AIAuditLog).where(AIAuditLog.is_deleted.is_(False))
        if capability is not None:
            stmt = stmt.where(AIAuditLog.capability == capability)
        if provider is not None:
            stmt = stmt.where(AIAuditLog.provider == provider)
        if call_id is not None:
            stmt = stmt.where(AIAuditLog.call_id == call_id)
        if incident_id is not None:
            stmt = stmt.where(AIAuditLog.incident_id == incident_id)
        stmt = (
            stmt.order_by(AIAuditLog.created_at.desc()).limit(limit).offset(offset)
        )
        return (await self._session.execute(stmt)).scalars().all()
