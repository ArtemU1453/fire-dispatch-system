"""Role & permission management (stage §3) — reuses existing RBAC tables.

Creates custom roles, assigns permissions to roles (through the existing
``role_permissions`` junction), manages permission groups, and audits changes.
Permissions themselves are read-only here (defined as data).
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.admin.audit import AdminAuditRecorder
from app.admin.models.entities import (
    PermissionGroup,
    PermissionGroupPermission,
)
from app.admin.schemas.admin import (
    PermissionGroupCreate,
    RoleCreate,
    RoleUpdate,
)
from app.admin.utils.actor import Actor
from app.core.exceptions import ConflictError, NotFoundError
from app.models.enums import AuditAction
from app.models.security import Permission, Role, RolePermission


class RoleService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AdminAuditRecorder(session)

    # ------------------------------------------------------------- roles
    async def list_roles(self) -> Sequence[Role]:
        stmt = (
            select(Role)
            .where(Role.is_deleted.is_(False))
            .order_by(Role.code)
            .options(
                selectinload(Role.permission_links).selectinload(
                    RolePermission.permission
                )
            )
        )
        return (await self._session.execute(stmt)).scalars().all()

    async def get_role(self, role_id: UUID) -> Role:
        stmt = (
            select(Role)
            .where(Role.id == role_id, Role.is_deleted.is_(False))
            .options(
                selectinload(Role.permission_links).selectinload(
                    RolePermission.permission
                )
            )
            .execution_options(populate_existing=True)
        )
        role = (await self._session.execute(stmt)).scalars().first()
        if role is None:
            raise NotFoundError("Role not found")
        return role

    async def create_role(self, data: RoleCreate) -> Role:
        actor = Actor(name=data.actor_name)
        if await self._role_exists(data.code):
            raise ConflictError(f"Role code already exists: {data.code}")
        role = Role(code=data.code, name=data.name, description=data.description)
        self._session.add(role)
        await self._session.flush()
        await self._set_permissions(role, data.permission_ids)
        self._audit.record(
            AuditAction.CREATE, "role", entity_id=role.id,
            changes={
                "code": data.code,
                "permissions": [str(p) for p in data.permission_ids],
            },
            actor=actor,
        )
        await self._session.flush()
        return await self.get_role(role.id)

    async def update_role(self, role_id: UUID, data: RoleUpdate) -> Role:
        role = await self.get_role(role_id)
        actor = Actor(name=data.actor_name)
        changes: dict = {}
        if data.name is not None and data.name != role.name:
            changes["name"] = {"old": role.name, "new": data.name}
            role.name = data.name
        if data.description is not None and data.description != role.description:
            changes["description"] = {"old": role.description, "new": data.description}
            role.description = data.description
        if data.permission_ids is not None:
            await self._set_permissions(role, data.permission_ids, replace=True)
            changes["permissions"] = {"new": [str(p) for p in data.permission_ids]}
        if changes:
            self._audit.record(
                AuditAction.UPDATE, "role", entity_id=role.id,
                changes=changes, reason=data.reason, actor=actor,
            )
        await self._session.flush()
        return await self.get_role(role_id)

    # ------------------------------------------------------- permissions
    async def list_permissions(self) -> Sequence[Permission]:
        stmt = (
            select(Permission)
            .where(Permission.is_deleted.is_(False))
            .order_by(Permission.code)
        )
        return (await self._session.execute(stmt)).scalars().all()

    # -------------------------------------------------- permission groups
    async def list_groups(self) -> Sequence[PermissionGroup]:
        stmt = (
            select(PermissionGroup)
            .where(PermissionGroup.is_deleted.is_(False))
            .order_by(PermissionGroup.code)
            .options(selectinload(PermissionGroup.members))
        )
        return (await self._session.execute(stmt)).scalars().all()

    async def create_group(
        self, data: PermissionGroupCreate
    ) -> PermissionGroup:
        actor = Actor(name=data.actor_name)
        group = PermissionGroup(
            code=data.code, name=data.name, description=data.description
        )
        for pid in data.permission_ids:
            group.members.append(PermissionGroupPermission(permission_id=pid))
        self._session.add(group)
        await self._session.flush()
        self._audit.record(
            AuditAction.CREATE, "permission_group", entity_id=group.id,
            changes={"code": data.code}, actor=actor,
        )
        await self._session.flush()
        return await self._require_group(group.id)

    async def group_permissions(
        self, group: PermissionGroup
    ) -> list[Permission]:
        ids = [m.permission_id for m in group.members if not m.is_deleted]
        if not ids:
            return []
        stmt = select(Permission).where(Permission.id.in_(ids))
        return list((await self._session.execute(stmt)).scalars().all())

    # ------------------------------------------------------------ helpers
    async def _set_permissions(
        self, role: Role, permission_ids, *, replace: bool = False
    ) -> None:
        # Query the junction directly — the relationship may be unloaded on a
        # freshly-created role (an async lazy load would fail).
        if replace:
            await self._session.execute(
                delete(RolePermission).where(RolePermission.role_id == role.id)
            )
            await self._session.flush()
            existing: set = set()
        else:
            existing = set(
                (
                    await self._session.execute(
                        select(RolePermission.permission_id).where(
                            RolePermission.role_id == role.id
                        )
                    )
                ).scalars().all()
            )
        for pid in permission_ids:
            if pid not in existing:
                self._session.add(
                    RolePermission(role_id=role.id, permission_id=pid)
                )
                existing.add(pid)

    async def _role_exists(self, code: str) -> bool:
        stmt = select(Role.id).where(Role.code == code, Role.is_deleted.is_(False))
        return (await self._session.execute(stmt)).scalars().first() is not None

    async def _require_group(self, group_id: UUID) -> PermissionGroup:
        stmt = (
            select(PermissionGroup)
            .where(PermissionGroup.id == group_id)
            .options(selectinload(PermissionGroup.members))
        )
        return (await self._session.execute(stmt)).scalars().first()
