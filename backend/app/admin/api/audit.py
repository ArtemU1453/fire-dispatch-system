"""Audit-log viewing endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query

from app.admin.deps import AuditServiceDep
from app.admin.schemas.admin import AuditResponse
from app.admin.utils.mapping import audit_to_response
from app.models.enums import AuditAction

router = APIRouter(tags=["admin: audit"])


@router.get("/audit", response_model=list[AuditResponse], summary="Audit log")
async def list_audit(
    service: AuditServiceDep,
    stream: str | None = Query(
        default=None,
        description="users | security | settings | integrations | directories",
    ),
    entity_type: str | None = Query(default=None),
    action: AuditAction | None = Query(default=None),
    user_id: UUID | None = Query(default=None),
    entity_id: UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[AuditResponse]:
    rows = await service.list_audit(
        stream=stream, entity_type=entity_type, action=action,
        user_id=user_id, entity_id=entity_id, limit=limit, offset=offset,
    )
    return [audit_to_response(r) for r in rows]
