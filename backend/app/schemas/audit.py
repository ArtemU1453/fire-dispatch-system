"""Schemas for :class:`AuditLog` (append-only)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from app.models.enums import AuditAction
from app.schemas.common import ResponseBase, SchemaBase


class AuditLogCreate(SchemaBase):
    user_id: UUID | None = None
    action: AuditAction
    entity_type: str
    entity_id: UUID | None = None
    changes: dict[str, Any] | None = None
    ip_address: str | None = None
    user_agent: str | None = None


class AuditLogUpdate(SchemaBase):
    # Audit records are immutable; this schema exists for API symmetry only.
    pass


class AuditLogResponse(ResponseBase):
    user_id: UUID | None = None
    action: AuditAction
    entity_type: str
    entity_id: UUID | None = None
    changes: dict[str, Any] | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    occurred_at: datetime
