"""Role, permission and permission-group endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from app.admin.deps import RoleServiceDep
from app.admin.schemas.admin import (
    PermissionGroupCreate,
    PermissionGroupResponse,
    PermissionResponse,
    RoleCreate,
    RoleResponse,
    RoleUpdate,
)
from app.admin.utils.mapping import (
    permission_group_to_response,
    permission_to_response,
    role_to_response,
)

router = APIRouter(tags=["admin: rbac"])


@router.get("/roles", response_model=list[RoleResponse], summary="List roles")
async def list_roles(service: RoleServiceDep) -> list[RoleResponse]:
    return [role_to_response(r) for r in await service.list_roles()]


@router.post(
    "/roles", response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED, summary="Create a role",
)
async def create_role(service: RoleServiceDep, data: RoleCreate) -> RoleResponse:
    return role_to_response(await service.create_role(data))


@router.get("/roles/{role_id}", response_model=RoleResponse, summary="Get a role")
async def get_role(service: RoleServiceDep, role_id: UUID) -> RoleResponse:
    return role_to_response(await service.get_role(role_id))


@router.patch(
    "/roles/{role_id}", response_model=RoleResponse, summary="Update a role"
)
async def update_role(
    service: RoleServiceDep, role_id: UUID, data: RoleUpdate
) -> RoleResponse:
    return role_to_response(await service.update_role(role_id, data))


@router.get(
    "/permissions", response_model=list[PermissionResponse],
    summary="List permissions",
)
async def list_permissions(service: RoleServiceDep) -> list[PermissionResponse]:
    return [permission_to_response(p) for p in await service.list_permissions()]


@router.get(
    "/permission-groups", response_model=list[PermissionGroupResponse],
    summary="List permission groups",
)
async def list_permission_groups(
    service: RoleServiceDep,
) -> list[PermissionGroupResponse]:
    groups = await service.list_groups()
    out = []
    for group in groups:
        perms = await service.group_permissions(group)
        out.append(permission_group_to_response(group, perms))
    return out


@router.post(
    "/permission-groups", response_model=PermissionGroupResponse,
    status_code=status.HTTP_201_CREATED, summary="Create a permission group",
)
async def create_permission_group(
    service: RoleServiceDep, data: PermissionGroupCreate
) -> PermissionGroupResponse:
    group = await service.create_group(data)
    perms = await service.group_permissions(group)
    return permission_group_to_response(group, perms)
