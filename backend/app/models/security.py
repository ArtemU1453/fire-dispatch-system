"""Authentication & RBAC entities.

``User`` ↔ ``Role`` ↔ ``Permission`` form a standard role-based access-control
model, normalized to 3NF with explicit junction tables (``UserRole``,
``RolePermission``) rather than array/JSON columns.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import CatalogEntity, Entity

if TYPE_CHECKING:
    from app.models.assets import Personnel


class User(Entity):
    """A system user (dispatcher, administrator, operator)."""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(128), nullable=False, unique=True, index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), nullable=False
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    personnel_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("personnel.id", ondelete="SET NULL"), nullable=True, index=True
    )

    personnel: Mapped[Personnel | None] = relationship()
    role_links: Mapped[list[UserRole]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Role(CatalogEntity):
    """A named role grouping a set of permissions."""

    __tablename__ = "roles"

    is_system: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )

    user_links: Mapped[list[UserRole]] = relationship(back_populates="role")
    permission_links: Mapped[list[RolePermission]] = relationship(
        back_populates="role", cascade="all, delete-orphan"
    )


class Permission(CatalogEntity):
    """A fine-grained permission (e.g. ``resource:read``, ``dispatch:create``)."""

    __tablename__ = "permissions"

    role_links: Mapped[list[RolePermission]] = relationship(
        back_populates="permission"
    )


class UserRole(Entity):
    """Junction: roles assigned to a user."""

    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True
    )

    user: Mapped[User] = relationship(back_populates="role_links")
    role: Mapped[Role] = relationship(back_populates="user_links")


class RolePermission(Entity):
    """Junction: permissions granted to a role."""

    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )

    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    permission_id: Mapped[UUID] = mapped_column(
        ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    role: Mapped[Role] = relationship(back_populates="permission_links")
    permission: Mapped[Permission] = relationship(back_populates="role_links")
