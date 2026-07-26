"""Pydantic schemas for the administration platform (stage §10)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from app.admin.models.enums import (
    AuthMethodKind,
    HealthStatus,
    IntegrationStatus,
    SettingCategory,
    SettingType,
)
from app.models.enums import AuditAction
from app.schemas.common import ResponseBase, SchemaBase


# --------------------------------------------------------------- RBAC ---
class PermissionResponse(ResponseBase):
    code: str
    name: str
    description: str | None = None


class RoleRef(SchemaBase):
    id: UUID
    code: str
    name: str


class RoleResponse(ResponseBase):
    code: str
    name: str
    description: str | None = None
    is_system: bool
    permissions: list[PermissionResponse] = []


class RoleCreate(SchemaBase):
    code: str
    name: str
    description: str | None = None
    permission_ids: list[UUID] = []
    actor_name: str | None = None


class RoleUpdate(SchemaBase):
    name: str | None = None
    description: str | None = None
    permission_ids: list[UUID] | None = None
    actor_name: str | None = None
    reason: str | None = None


class PermissionGroupResponse(ResponseBase):
    code: str
    name: str
    description: str | None = None
    is_system: bool
    permissions: list[PermissionResponse] = []


class PermissionGroupCreate(SchemaBase):
    code: str
    name: str
    description: str | None = None
    permission_ids: list[UUID] = []
    actor_name: str | None = None


# --------------------------------------------------------------- users ---
class UserResponse(ResponseBase):
    username: str
    email: str
    full_name: str | None = None
    is_active: bool
    is_superuser: bool
    last_login_at: datetime | None = None
    roles: list[RoleRef] = []


class UserCreate(SchemaBase):
    username: str
    email: str
    password: str
    full_name: str | None = None
    is_active: bool = True
    is_superuser: bool = False
    role_ids: list[UUID] = []
    actor_name: str | None = None
    reason: str | None = None


class UserUpdate(SchemaBase):
    email: str | None = None
    full_name: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    password: str | None = None
    role_ids: list[UUID] | None = None
    actor_name: str | None = None
    reason: str | None = None


# ------------------------------------------------------------ settings ---
class SettingResponse(ResponseBase):
    key: str
    value: str | None = None
    value_type: SettingType
    category: SettingCategory
    description: str | None = None
    version: int
    is_secret: bool
    is_active: bool


class SettingCreate(SchemaBase):
    key: str
    value: str | None = None
    value_type: SettingType = SettingType.STRING
    category: SettingCategory = SettingCategory.GENERAL
    description: str | None = None
    is_secret: bool = False
    actor_name: str | None = None
    reason: str | None = None


class SettingUpdate(SchemaBase):
    value: str | None = None
    description: str | None = None
    is_active: bool | None = None
    actor_name: str | None = None
    reason: str | None = None


class SettingHistoryResponse(ResponseBase):
    key: str
    old_value: str | None = None
    new_value: str | None = None
    version: int
    changed_by_name: str | None = None
    reason: str | None = None
    occurred_at: datetime


# --------------------------------------------------------- directories ---
class DirectoryItemResponse(SchemaBase):
    id: UUID
    code: str
    name: str
    description: str | None = None
    is_deleted: bool
    extra: dict[str, Any] = {}


class DirectoryItemCreate(SchemaBase):
    code: str
    name: str
    description: str | None = None
    extra: dict[str, Any] = {}
    actor_name: str | None = None


class DirectoryItemUpdate(SchemaBase):
    name: str | None = None
    description: str | None = None
    extra: dict[str, Any] = {}
    actor_name: str | None = None
    reason: str | None = None


class DirectoryInfo(SchemaBase):
    name: str
    label: str
    editable_fields: list[str] = []


# -------------------------------------------------------- integrations ---
class IntegrationProviderResponse(ResponseBase):
    code: str
    name: str
    description: str | None = None
    kind: str | None = None


class IntegrationConfigResponse(SchemaBase):
    key: str
    value: str | None = None  # masked when is_secret
    is_secret: bool


class IntegrationHealthResponse(SchemaBase):
    status: HealthStatus
    latency_ms: int | None = None
    detail: str | None = None
    checked_at: datetime | None = None


class IntegrationResponse(ResponseBase):
    code: str
    name: str
    provider_id: UUID | None = None
    status: IntegrationStatus
    is_enabled: bool
    description: str | None = None
    has_secret: bool
    config: dict[str, Any] | None = None
    configurations: list[IntegrationConfigResponse] = []
    last_health: IntegrationHealthResponse | None = None


class IntegrationConfigInput(SchemaBase):
    key: str
    value: str | None = None
    is_secret: bool = False


class IntegrationCreate(SchemaBase):
    code: str
    name: str
    provider_id: UUID | None = None
    description: str | None = None
    is_enabled: bool = False
    config: dict[str, Any] | None = None
    secret_ref: str | None = None
    configurations: list[IntegrationConfigInput] = []
    actor_name: str | None = None


class IntegrationUpdate(SchemaBase):
    name: str | None = None
    provider_id: UUID | None = None
    description: str | None = None
    is_enabled: bool | None = None
    status: IntegrationStatus | None = None
    config: dict[str, Any] | None = None
    secret_ref: str | None = None
    configurations: list[IntegrationConfigInput] | None = None
    actor_name: str | None = None
    reason: str | None = None


# ---------------------------------------------------------------- audit ---
class AuditResponse(ResponseBase):
    user_id: UUID | None = None
    action: AuditAction
    entity_type: str
    entity_id: UUID | None = None
    changes: dict[str, Any] | None = None
    ip_address: str | None = None
    occurred_at: datetime


# ------------------------------------------------------- auth methods ---
class AuthMethodResponse(ResponseBase):
    code: str
    name: str
    kind: AuthMethodKind
    is_enabled: bool
    is_default: bool
    config: dict[str, Any] | None = None


# ------------------------------------------------------------ AI admin ---
class AIProviderAdminResponse(SchemaBase):
    name: str
    model: str
    model_version: str
    capabilities: list[str] = []
    healthy: bool
    is_default: bool
    is_enabled: bool


class AISettingsResponse(SchemaBase):
    default_provider: str | None = None
    providers: list[AIProviderAdminResponse] = []
    parameters: dict[str, Any] = {}
