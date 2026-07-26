"""User & permission-check endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.admin.deps import RBACServiceDep, UserServiceDep
from app.admin.schemas.admin import (
    AuthMethodResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.admin.utils.mapping import auth_method_to_response, user_to_response

router = APIRouter(tags=["admin: users"])


@router.get("/users", response_model=list[UserResponse], summary="List users")
async def list_users(
    service: UserServiceDep,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[UserResponse]:
    users = await service.list_users(limit=limit, offset=offset)
    return [user_to_response(u) for u in users]


@router.post(
    "/users", response_model=UserResponse,
    status_code=status.HTTP_201_CREATED, summary="Create a user",
)
async def create_user(
    service: UserServiceDep, data: UserCreate
) -> UserResponse:
    return user_to_response(await service.create_user(data))


@router.get("/users/{user_id}", response_model=UserResponse, summary="Get a user")
async def get_user(service: UserServiceDep, user_id: UUID) -> UserResponse:
    return user_to_response(await service.get_user(user_id))


@router.patch(
    "/users/{user_id}", response_model=UserResponse, summary="Update a user"
)
async def update_user(
    service: UserServiceDep, user_id: UUID, data: UserUpdate
) -> UserResponse:
    return user_to_response(await service.update_user(user_id, data))


@router.get(
    "/users/{user_id}/permissions", response_model=list[str],
    summary="A user's effective permissions",
)
async def user_permissions(rbac: RBACServiceDep, user_id: UUID) -> list[str]:
    return sorted(await rbac.effective_permissions(user_id))


@router.get(
    "/auth-methods", response_model=list[AuthMethodResponse],
    summary="List authentication methods",
)
async def list_auth_methods(
    service: UserServiceDep,
) -> list[AuthMethodResponse]:
    methods = await service.list_auth_methods()
    return [auth_method_to_response(m) for m in methods]
