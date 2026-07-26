"""User management (stage §2) — reuses the existing ``users`` model.

Creates and edits users, hashes passwords (validating them against the active
password policy), assigns roles through the existing ``user_roles`` junction, and
audits every change. It never modifies the ``User`` model definition — only rows.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.admin.audit import AdminAuditRecorder, diff
from app.admin.models.entities import AuthenticationMethod, PasswordPolicy
from app.admin.schemas.admin import UserCreate, UserUpdate
from app.admin.utils.actor import Actor
from app.admin.utils.passwords import (
    PasswordRules,
    hash_password,
    validate_password,
)
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.enums import AuditAction
from app.models.security import User, UserRole

_USER_TRACKED = ("email", "full_name", "is_active", "is_superuser")


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AdminAuditRecorder(session)

    async def list_users(
        self, *, limit: int = 100, offset: int = 0
    ) -> Sequence[User]:
        stmt = (
            select(User)
            .where(User.is_deleted.is_(False))
            .order_by(User.username)
            .limit(limit)
            .offset(offset)
            .options(selectinload(User.role_links).selectinload(UserRole.role))
        )
        return (await self._session.execute(stmt)).scalars().all()

    async def get_user(self, user_id: UUID) -> User:
        stmt = (
            select(User)
            .where(User.id == user_id, User.is_deleted.is_(False))
            .options(selectinload(User.role_links).selectinload(UserRole.role))
            .execution_options(populate_existing=True)
        )
        user = (await self._session.execute(stmt)).scalars().first()
        if user is None:
            raise NotFoundError("User not found")
        return user

    async def create_user(self, data: UserCreate) -> User:
        actor = Actor(name=data.actor_name)
        if await self._exists(User.username == data.username):
            raise ConflictError(f"Username already exists: {data.username}")
        if await self._exists(User.email == data.email):
            raise ConflictError(f"Email already exists: {data.email}")
        await self._check_password(data.password)

        user = User(
            username=data.username,
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            is_active=data.is_active,
            is_superuser=data.is_superuser,
        )
        self._session.add(user)
        await self._session.flush()
        await self._set_roles(user, data.role_ids)
        self._audit.record(
            AuditAction.CREATE, "user", entity_id=user.id,
            changes={"username": data.username, "email": data.email},
            reason=data.reason, actor=actor,
        )
        await self._session.flush()
        return await self.get_user(user.id)

    async def update_user(self, user_id: UUID, data: UserUpdate) -> User:
        user = await self.get_user(user_id)
        actor = Actor(name=data.actor_name)
        payload = data.model_dump(
            exclude_unset=True,
            exclude={"actor_name", "reason", "password", "role_ids"},
        )
        before = {f: getattr(user, f) for f in _USER_TRACKED}
        for field in _USER_TRACKED:
            if field in payload:
                setattr(user, field, payload[field])
        after = {f: getattr(user, f) for f in _USER_TRACKED}
        changes = diff(before, after)

        if data.password is not None:
            await self._check_password(data.password)
            user.hashed_password = hash_password(data.password)
            changes["password"] = {"old": "***", "new": "***"}
        if data.role_ids is not None:
            await self._set_roles(user, data.role_ids, replace=True)
            changes["roles"] = {"new": [str(r) for r in data.role_ids]}

        if changes:
            self._audit.record(
                AuditAction.UPDATE, "user", entity_id=user.id,
                changes=changes, reason=data.reason, actor=actor,
            )
        await self._session.flush()
        return await self.get_user(user_id)

    async def list_auth_methods(self) -> Sequence[AuthenticationMethod]:
        stmt = (
            select(AuthenticationMethod)
            .where(AuthenticationMethod.is_deleted.is_(False))
            .order_by(AuthenticationMethod.code)
        )
        return (await self._session.execute(stmt)).scalars().all()

    # ------------------------------------------------------------ helpers
    async def _set_roles(
        self, user: User, role_ids, *, replace: bool = False
    ) -> None:
        # Query the junction directly — the relationship may be unloaded on a
        # freshly-created user (an async lazy load would fail).
        if replace:
            await self._session.execute(
                delete(UserRole).where(UserRole.user_id == user.id)
            )
            await self._session.flush()
            existing: set = set()
        else:
            existing = set(
                (
                    await self._session.execute(
                        select(UserRole.role_id).where(
                            UserRole.user_id == user.id
                        )
                    )
                ).scalars().all()
            )
        for role_id in role_ids:
            if role_id not in existing:
                self._session.add(UserRole(user_id=user.id, role_id=role_id))
                existing.add(role_id)

    async def _check_password(self, password: str) -> None:
        rules = await self._active_rules()
        problems = validate_password(password, rules)
        if problems:
            raise ValidationError(
                "Пароль не соответствует политике: " + "; ".join(problems)
            )

    async def _active_rules(self) -> PasswordRules:
        stmt = (
            select(PasswordPolicy)
            .where(
                PasswordPolicy.is_active.is_(True),
                PasswordPolicy.is_deleted.is_(False),
            )
            .order_by(PasswordPolicy.is_default.desc())
        )
        policy = (await self._session.execute(stmt)).scalars().first()
        if policy is None:
            return PasswordRules()
        return PasswordRules(
            min_length=policy.min_length,
            require_uppercase=policy.require_uppercase,
            require_lowercase=policy.require_lowercase,
            require_digit=policy.require_digit,
            require_special=policy.require_special,
        )

    async def _exists(self, condition) -> bool:
        stmt = select(User.id).where(condition, User.is_deleted.is_(False))
        return (await self._session.execute(stmt)).scalars().first() is not None
