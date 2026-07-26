"""RBAC — role-based access control (stage §3).

A user gets permissions **through roles**; a role holds a set of permissions;
permissions are stored in the database and custom roles can be created. This
service resolves a user's effective permissions and answers permission checks.

It reuses the existing ``users`` / ``roles`` / ``permissions`` / ``user_roles`` /
``role_permissions`` tables **unchanged**.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.security import (
    Permission,
    RolePermission,
    User,
    UserRole,
)


class RBACService:
    """Resolves and checks a user's permissions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def effective_permissions(self, user_id: UUID) -> set[str]:
        """The set of permission codes a user holds through their roles."""
        user = await self._session.get(User, user_id)
        if user is None:
            raise NotFoundError("User not found")
        if user.is_superuser:
            return {p.code for p in await self.list_permissions()}
        stmt = (
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .where(
                UserRole.user_id == user_id,
                Permission.is_deleted.is_(False),
            )
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return set(rows)

    async def has_permission(self, user_id: UUID, code: str) -> bool:
        user = await self._session.get(User, user_id)
        if user is None:
            return False
        if user.is_superuser:
            return True
        return code in await self.effective_permissions(user_id)

    async def require_permission(self, user_id: UUID, code: str) -> None:
        from app.admin.exceptions import AuthorizationError

        if not await self.has_permission(user_id, code):
            raise AuthorizationError(f"Missing permission: {code}")

    async def list_permissions(self) -> Sequence[Permission]:
        stmt = (
            select(Permission)
            .where(Permission.is_deleted.is_(False))
            .order_by(Permission.code)
        )
        return (await self._session.execute(stmt)).scalars().all()
