"""RBAC access control for the Crisis Management Platform (Stage 20 §13).

Reuses the existing Administration RBAC service. Permission codes distinguish
read vs command actions; roles (dispatcher, РТП, начальник смены, оперативный
штаб, администратор) are granted the appropriate codes in the RBAC data.

Consistent with the rest of the system, access is **open when no user is
identified** (no authentication layer is wired yet — see the Stage 16 security
audit); when a user id is supplied, the permission is enforced.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.rbac.service import RBACService

# Permission codes used by the crisis platform.
PERM_VIEW = "crisis.view"
PERM_MANAGE = "crisis.manage"          # create/update operations, sectors, plan
PERM_COMMAND = "crisis.command"        # headquarters: commanders, decisions
PERM_RESOURCE = "crisis.resource"      # resource groups & relocation


class CrisisAccess:
    """Thin RBAC gate over the existing :class:`RBACService`."""

    def __init__(self, session: AsyncSession) -> None:
        self._rbac = RBACService(session)

    async def require(self, user_id: UUID | None, permission: str) -> None:
        """Enforce *permission* for *user_id*; open when no user is identified."""
        if user_id is None:
            return
        await self._rbac.require_permission(user_id, permission)

    async def can(self, user_id: UUID | None, permission: str) -> bool:
        if user_id is None:
            return True
        return await self._rbac.has_permission(user_id, permission)
