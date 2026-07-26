"""Mapping between administration ORM objects and API schemas.

Secret values are **masked** here (settings marked secret, secret integration
configs) so they never leave the service in clear text.
"""

from __future__ import annotations

from app.admin.models.entities import (
    AuthenticationMethod,
    Integration,
    IntegrationConfiguration,
    IntegrationHealthCheck,
    IntegrationProvider,
    PermissionGroup,
    Setting,
    SettingHistory,
)
from app.admin.schemas.admin import (
    AuditResponse,
    AuthMethodResponse,
    DirectoryItemResponse,
    IntegrationConfigResponse,
    IntegrationHealthResponse,
    IntegrationProviderResponse,
    IntegrationResponse,
    PermissionGroupResponse,
    PermissionResponse,
    RoleRef,
    RoleResponse,
    SettingHistoryResponse,
    SettingResponse,
    UserResponse,
)
from app.admin.services.directory_service import item_extra
from app.models.audit import AuditLog
from app.models.security import Permission, Role, User

_MASK = "***"


def permission_to_response(p: Permission) -> PermissionResponse:
    return PermissionResponse.model_validate(p)


def role_to_response(role: Role) -> RoleResponse:
    permissions = [
        permission_to_response(link.permission)
        for link in role.permission_links
        if not link.is_deleted and link.permission is not None
    ]
    return RoleResponse(
        id=role.id, created_at=role.created_at, updated_at=role.updated_at,
        is_deleted=role.is_deleted, code=role.code, name=role.name,
        description=role.description, is_system=role.is_system,
        permissions=permissions,
    )


def user_to_response(user: User) -> UserResponse:
    roles = [
        RoleRef(id=link.role.id, code=link.role.code, name=link.role.name)
        for link in user.role_links
        if not link.is_deleted and link.role is not None
    ]
    return UserResponse(
        id=user.id, created_at=user.created_at, updated_at=user.updated_at,
        is_deleted=user.is_deleted, username=user.username, email=user.email,
        full_name=user.full_name, is_active=user.is_active,
        is_superuser=user.is_superuser, last_login_at=user.last_login_at,
        roles=roles,
    )


def permission_group_to_response(
    group: PermissionGroup, permissions: list[Permission]
) -> PermissionGroupResponse:
    return PermissionGroupResponse(
        id=group.id, created_at=group.created_at, updated_at=group.updated_at,
        is_deleted=group.is_deleted, code=group.code, name=group.name,
        description=group.description, is_system=group.is_system,
        permissions=[permission_to_response(p) for p in permissions],
    )


def setting_to_response(setting: Setting) -> SettingResponse:
    value = _MASK if setting.is_secret else setting.value
    return SettingResponse(
        id=setting.id, created_at=setting.created_at,
        updated_at=setting.updated_at, is_deleted=setting.is_deleted,
        key=setting.key, value=value, value_type=setting.value_type,
        category=setting.category, description=setting.description,
        version=setting.version, is_secret=setting.is_secret,
        is_active=setting.is_active,
    )


def setting_history_to_response(h: SettingHistory) -> SettingHistoryResponse:
    return SettingHistoryResponse.model_validate(h)


def directory_item_to_response(item, model: type) -> DirectoryItemResponse:
    return DirectoryItemResponse(
        id=item.id, code=item.code, name=item.name,
        description=item.description, is_deleted=item.is_deleted,
        extra=item_extra(item, model),
    )


def _config_to_response(
    cfg: IntegrationConfiguration,
) -> IntegrationConfigResponse:
    return IntegrationConfigResponse(
        key=cfg.key,
        value=_MASK if cfg.is_secret else cfg.value,
        is_secret=cfg.is_secret,
    )


def health_to_response(
    check: IntegrationHealthCheck | None,
) -> IntegrationHealthResponse | None:
    if check is None:
        return None
    return IntegrationHealthResponse(
        status=check.status, latency_ms=check.latency_ms,
        detail=check.detail, checked_at=check.checked_at,
    )


def integration_to_response(
    integration: Integration, *, latest_health: IntegrationHealthCheck | None
) -> IntegrationResponse:
    configs = [
        _config_to_response(c)
        for c in integration.configurations
        if not c.is_deleted
    ]
    has_secret = bool(integration.secret_ref) or any(
        c.is_secret for c in integration.configurations if not c.is_deleted
    )
    return IntegrationResponse(
        id=integration.id, created_at=integration.created_at,
        updated_at=integration.updated_at, is_deleted=integration.is_deleted,
        code=integration.code, name=integration.name,
        provider_id=integration.provider_id, status=integration.status,
        is_enabled=integration.is_enabled, description=integration.description,
        has_secret=has_secret, config=integration.config,
        configurations=configs, last_health=health_to_response(latest_health),
    )


def integration_provider_to_response(
    p: IntegrationProvider,
) -> IntegrationProviderResponse:
    return IntegrationProviderResponse.model_validate(p)


def auth_method_to_response(m: AuthenticationMethod) -> AuthMethodResponse:
    return AuthMethodResponse.model_validate(m)


def audit_to_response(entry: AuditLog) -> AuditResponse:
    return AuditResponse.model_validate(entry)
