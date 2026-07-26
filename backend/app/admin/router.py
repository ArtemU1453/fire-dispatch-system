"""Aggregate router for the administration module (prefix ``/admin``)."""

from __future__ import annotations

from fastapi import APIRouter

from app.admin.api import (
    ai,
    audit,
    directories,
    integrations,
    roles,
    settings,
    users,
)

admin_router = APIRouter(prefix="/admin")
admin_router.include_router(users.router)
admin_router.include_router(roles.router)
admin_router.include_router(settings.router)
admin_router.include_router(directories.router)
admin_router.include_router(integrations.router)
admin_router.include_router(audit.router)
admin_router.include_router(ai.router)
