"""Schemas for authentication & RBAC entities.

Passwords are accepted in plain text only on input (``password``) and are never
returned; the stored hash is not part of any response schema.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.schemas.catalog import (
    CatalogCreateBase,
    CatalogResponseBase,
    CatalogUpdateBase,
)
from app.schemas.common import ResponseBase, SchemaBase

# ---------------------------------------------------------------------- user --


class UserCreate(SchemaBase):
    username: str
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None
    is_active: bool = True
    is_superuser: bool = False
    personnel_id: UUID | None = None


class UserUpdate(SchemaBase):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8)
    full_name: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    personnel_id: UUID | None = None


class UserResponse(ResponseBase):
    username: str
    email: EmailStr
    full_name: str | None = None
    is_active: bool
    is_superuser: bool
    last_login_at: datetime | None = None
    personnel_id: UUID | None = None


# ---------------------------------------------------------------------- role --


class RoleCreate(CatalogCreateBase):
    is_system: bool = False


class RoleUpdate(CatalogUpdateBase):
    is_system: bool | None = None


class RoleResponse(CatalogResponseBase):
    is_system: bool


# --------------------------------------------------------------- permission --


class PermissionCreate(CatalogCreateBase):
    pass


class PermissionUpdate(CatalogUpdateBase):
    pass


class PermissionResponse(CatalogResponseBase):
    pass


# ---------------------------------------------------------------- junctions --


class UserRoleCreate(SchemaBase):
    user_id: UUID
    role_id: UUID


class UserRoleUpdate(SchemaBase):
    role_id: UUID | None = None


class UserRoleResponse(ResponseBase):
    user_id: UUID
    role_id: UUID


class RolePermissionCreate(SchemaBase):
    role_id: UUID
    permission_id: UUID


class RolePermissionUpdate(SchemaBase):
    permission_id: UUID | None = None


class RolePermissionResponse(ResponseBase):
    role_id: UUID
    permission_id: UUID
