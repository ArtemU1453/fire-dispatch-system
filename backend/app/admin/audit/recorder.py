"""Administrative audit recorder (stage §11).

Reuses the existing ``audit_logs`` trail (``AuditLog`` / ``AuditAction``) — no new
audit table is introduced. Every administrative change records **who** made it,
**when**, the **old → new** values (as a JSONB diff) and, when provided, the
**reason** for the change (stored under the ``_reason`` key of the diff).

The ``entity_type`` distinguishes the log streams the admin UI needs (user, role,
permission, setting, directory, integration, …), and ``action`` classifies it.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.utils.actor import Actor
from app.models.audit import AuditLog
from app.models.enums import AuditAction


def diff(old: dict[str, Any], new: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Build a ``{field: {old, new}}`` diff for changed keys only."""
    changes: dict[str, dict[str, Any]] = {}
    for key, new_value in new.items():
        old_value = old.get(key)
        if old_value != new_value:
            changes[key] = {"old": old_value, "new": new_value}
    return changes


class AdminAuditRecorder:
    """Writes ``AuditLog`` rows for administrative actions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def record(
        self,
        action: AuditAction,
        entity_type: str,
        *,
        entity_id: UUID | None = None,
        changes: dict[str, Any] | None = None,
        reason: str | None = None,
        actor: Actor | None = None,
    ) -> AuditLog:
        actor = actor or Actor()
        payload: dict[str, Any] | None = dict(changes) if changes else None
        if reason:
            payload = payload or {}
            payload["_reason"] = reason
        if actor.name:
            payload = payload or {}
            payload.setdefault("_actor_name", actor.name)
        entry = AuditLog(
            user_id=actor.user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            changes=payload,
            ip_address=actor.ip_address,
        )
        self._session.add(entry)
        return entry
