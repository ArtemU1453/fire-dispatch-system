"""Audit-log viewing (stage §8) — reads the existing ``audit_logs`` trail.

Provides filtered / searchable access to the audit log: by user-action stream,
security, integrations, settings changes, and errors, plus filters by user,
entity and action. The named **streams** map to ``entity_type`` prefixes so the
admin UI can present separate journals without a separate table per stream.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.enums import AuditAction

# Named log streams → the entity_type values they include.
STREAMS: dict[str, tuple[str, ...]] = {
    "users": ("user", "role", "permission", "permission_group"),
    "security": ("user", "role", "permission", "auth_method", "session"),
    "settings": ("setting",),
    "integrations": ("integration",),
    "directories": ("directory:",),  # prefix match
}


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_audit(
        self,
        *,
        stream: str | None = None,
        entity_type: str | None = None,
        action: AuditAction | None = None,
        user_id: UUID | None = None,
        entity_id: UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[AuditLog]:
        stmt = select(AuditLog)
        if stream and stream in STREAMS:
            values = STREAMS[stream]
            conds = []
            for v in values:
                if v.endswith(":"):
                    conds.append(AuditLog.entity_type.like(f"{v}%"))
                else:
                    conds.append(AuditLog.entity_type == v)
            stmt = stmt.where(or_(*conds))
        if entity_type is not None:
            stmt = stmt.where(AuditLog.entity_type == entity_type)
        if action is not None:
            stmt = stmt.where(AuditLog.action == action)
        if user_id is not None:
            stmt = stmt.where(AuditLog.user_id == user_id)
        if entity_id is not None:
            stmt = stmt.where(AuditLog.entity_id == entity_id)
        stmt = (
            stmt.order_by(AuditLog.occurred_at.desc()).limit(limit).offset(offset)
        )
        return (await self._session.execute(stmt)).scalars().all()
