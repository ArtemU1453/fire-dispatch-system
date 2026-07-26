"""Analytics access control (stage §11).

Reuses the Administration module's RBAC (public service) — analytics defines no
new permission model. When a user is identified, a required permission is checked
(superuser bypasses). With no user context (no auth backend wired yet), access is
permitted so the platform is usable in development; production wires a real
authenticated principal.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.rbac import RBACService


class AnalyticsAccess:
    def __init__(self, session: AsyncSession) -> None:
        self._rbac = RBACService(session)

    async def require(self, user_id: UUID | None, permission: str) -> None:
        if user_id is None:
            return
        await self._rbac.require_permission(user_id, permission)

    async def has(self, user_id: UUID | None, permission: str) -> bool:
        if user_id is None:
            return True
        return await self._rbac.has_permission(user_id, permission)
