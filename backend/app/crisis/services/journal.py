"""Unified, immutable operational journal (Stage 20 §8).

Every significant action and decision is appended here. The journal is
**append-only**: this service exposes only ``append`` and read methods — there
is no update or delete, so entries are immutable once written.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crisis.models.entities import JournalEntry
from app.crisis.models.enums import JournalKind
from app.crisis.repositories.repositories import JournalRepository
from app.repositories.base import QuerySpec


class JournalService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = JournalRepository(session)

    async def append(
        self,
        operation_id: UUID,
        *,
        kind: JournalKind,
        message: str,
        actor_ref: str | None = None,
        rationale: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> JournalEntry:
        return await self._repo.add(
            JournalEntry(
                operation_id=operation_id,
                kind=kind.value,
                message=message,
                actor_ref=actor_ref,
                rationale=rationale,
                payload=payload,
            )
        )

    async def timeline(
        self, operation_id: UUID, *, kind: JournalKind | None = None, limit: int = 200
    ) -> list[JournalEntry]:
        filters: dict[str, Any] = {"operation_id": operation_id}
        if kind is not None:
            filters["kind"] = kind.value
        spec = QuerySpec(filters=filters, order_by=["created_at"], limit=limit)
        return list(await self._repo.list(spec))
