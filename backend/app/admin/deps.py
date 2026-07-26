"""Administration dependency providers (Dependency Injection wiring)."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.admin.rbac import RBACService
from app.admin.services import (
    AIAdminService,
    AuditService,
    DirectoryService,
    IntegrationService,
    RoleService,
    SettingsService,
    UserService,
)
from app.api.deps import SessionDep


def get_user_service(session: SessionDep) -> UserService:
    return UserService(session)


def get_role_service(session: SessionDep) -> RoleService:
    return RoleService(session)


def get_rbac_service(session: SessionDep) -> RBACService:
    return RBACService(session)


def get_settings_service(session: SessionDep) -> SettingsService:
    return SettingsService(session)


def get_directory_service(session: SessionDep) -> DirectoryService:
    return DirectoryService(session)


def get_integration_service(session: SessionDep) -> IntegrationService:
    return IntegrationService(session)


def get_audit_service(session: SessionDep) -> AuditService:
    return AuditService(session)


def get_ai_admin_service(session: SessionDep) -> AIAdminService:
    return AIAdminService(session)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
RoleServiceDep = Annotated[RoleService, Depends(get_role_service)]
RBACServiceDep = Annotated[RBACService, Depends(get_rbac_service)]
SettingsServiceDep = Annotated[SettingsService, Depends(get_settings_service)]
DirectoryServiceDep = Annotated[DirectoryService, Depends(get_directory_service)]
IntegrationServiceDep = Annotated[
    IntegrationService, Depends(get_integration_service)
]
AuditServiceDep = Annotated[AuditService, Depends(get_audit_service)]
AIAdminServiceDep = Annotated[AIAdminService, Depends(get_ai_admin_service)]
