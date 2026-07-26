"""ORM models for the administration platform.

Adds the *administrative* concepts on top of the existing model — it **reuses**
the Stage-2 RBAC tables (``users`` / ``roles`` / ``permissions`` /
``user_roles`` / ``role_permissions``) and the existing ``audit_logs`` trail
**without modifying them**, and adds: permission **groups**, **account statuses**,
**user sessions**, **password policies**, **authentication methods**, system
**settings** (+ history), and **integrations** (+ providers, configurations,
health checks).

Nothing here contains dispatch business logic; it is pure administration.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.admin.models.enums import (
    AuthMethodKind,
    HealthStatus,
    IntegrationStatus,
    SettingCategory,
    SettingType,
)
from app.admin.models.types import (
    auth_method_kind_enum,
    health_status_enum,
    integration_status_enum,
    setting_category_enum,
    setting_type_enum,
)
from app.models.base import CatalogEntity, Entity


# ------------------------------------------------------------------- RBAC ---
class PermissionGroup(CatalogEntity):
    """A named bundle of permissions (eases assembling roles)."""

    __tablename__ = "permission_groups"

    is_system: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )

    members: Mapped[list[PermissionGroupPermission]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )


class PermissionGroupPermission(Entity):
    """Junction: permissions belonging to a permission group."""

    __tablename__ = "permission_group_permissions"
    __table_args__ = (
        UniqueConstraint(
            "group_id", "permission_id", name="uq_permission_group_permission"
        ),
    )

    group_id: Mapped[UUID] = mapped_column(
        ForeignKey("permission_groups.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    permission_id: Mapped[UUID] = mapped_column(
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    group: Mapped[PermissionGroup] = relationship(back_populates="members")


# --------------------------------------------------------------- accounts ---
class AccountStatus(CatalogEntity):
    """A manageable account-status catalog (active / disabled / locked / …)."""

    __tablename__ = "account_statuses"

    login_allowed: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), nullable=False
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )


class UserSession(Entity):
    """A record of a user session (no real auth backend at this stage)."""

    __tablename__ = "user_sessions"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_token: Mapped[str] = mapped_column(
        String(128), nullable=False, unique=True, index=True
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at_session: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), nullable=False, index=True
    )


class PasswordPolicy(Entity):
    """A configurable password policy (only its rules — no secrets)."""

    __tablename__ = "password_policies"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    min_length: Mapped[int] = mapped_column(
        Integer, server_default="8", nullable=False
    )
    require_uppercase: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), nullable=False
    )
    require_lowercase: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), nullable=False
    )
    require_digit: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), nullable=False
    )
    require_special: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    max_age_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    history_depth: Mapped[int] = mapped_column(
        Integer, server_default="0", nullable=False
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), nullable=False
    )


class AuthenticationMethod(Entity):
    """An authentication method — external kinds are architecture only.

    LDAP / Active Directory / OIDC / SAML are represented so they can be enabled
    later, but **none are implemented** at this stage (constraints).
    """

    __tablename__ = "authentication_methods"

    code: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[AuthMethodKind] = mapped_column(
        auth_method_kind_enum,
        server_default=AuthMethodKind.PASSWORD.value, nullable=False,
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    # Non-secret connection parameters only (host, base DN, issuer URL…).
    config: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


# --------------------------------------------------------------- settings ---
class Setting(Entity):
    """A single system setting (typed, categorised, versioned)."""

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_type: Mapped[SettingType] = mapped_column(
        setting_type_enum, server_default=SettingType.STRING.value, nullable=False
    )
    category: Mapped[SettingCategory] = mapped_column(
        setting_category_enum, server_default=SettingCategory.GENERAL.value,
        nullable=False, index=True,
    )
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    version: Mapped[int] = mapped_column(
        Integer, server_default="1", nullable=False
    )
    is_secret: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), nullable=False
    )

    history: Mapped[list[SettingHistory]] = relationship(
        back_populates="setting", cascade="all, delete-orphan"
    )


class SettingHistory(Entity):
    """Append-only change history for a setting (old → new, who, when, why)."""

    __tablename__ = "app_setting_history"

    setting_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("app_settings.id", ondelete="CASCADE"),
        nullable=True, index=True,
    )
    key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    changed_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    changed_by_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(512), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    setting: Mapped[Setting | None] = relationship(back_populates="history")


# ----------------------------------------------------------- integrations ---
class IntegrationProvider(CatalogEntity):
    """A catalog of integration providers (telephony, GIS, SMS gateway, …)."""

    __tablename__ = "integration_providers"

    kind: Mapped[str | None] = mapped_column(String(64), nullable=True)


class Integration(Entity):
    """A configured integration with an external system.

    Connection parameters live in ``config`` (JSONB, **non-secret only**);
    secrets are referenced by ``secret_ref`` (a pointer into a future secret
    manager) — the platform **never stores secrets in clear text**.
    """

    __tablename__ = "integrations"

    code: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("integration_providers.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    status: Mapped[IntegrationStatus] = mapped_column(
        integration_status_enum,
        server_default=IntegrationStatus.INACTIVE.value, nullable=False, index=True,
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    secret_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    config: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    provider: Mapped[IntegrationProvider | None] = relationship(lazy="raise")
    configurations: Mapped[list[IntegrationConfiguration]] = relationship(
        back_populates="integration", cascade="all, delete-orphan"
    )
    health_checks: Mapped[list[IntegrationHealthCheck]] = relationship(
        back_populates="integration", cascade="all, delete-orphan"
    )


class IntegrationConfiguration(Entity):
    """A key/value configuration entry for an integration.

    ``is_secret`` marks a value that must be resolved through a secret manager;
    for those, ``value`` holds a **reference**, never the secret itself.
    """

    __tablename__ = "integration_configurations"
    __table_args__ = (
        UniqueConstraint(
            "integration_id", "key", name="uq_integration_configuration_key"
        ),
    )

    integration_id: Mapped[UUID] = mapped_column(
        ForeignKey("integrations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_secret: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )

    integration: Mapped[Integration] = relationship(back_populates="configurations")


class IntegrationHealthCheck(Entity):
    """The result of a health check against an integration."""

    __tablename__ = "integration_health_checks"

    integration_id: Mapped[UUID] = mapped_column(
        ForeignKey("integrations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    status: Mapped[HealthStatus] = mapped_column(
        health_status_enum, server_default=HealthStatus.UNKNOWN.value,
        nullable=False,
    )
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detail: Mapped[str | None] = mapped_column(String(512), nullable=True)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    integration: Mapped[Integration] = relationship(back_populates="health_checks")
