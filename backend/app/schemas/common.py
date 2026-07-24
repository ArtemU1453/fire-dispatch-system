"""Shared Pydantic v2 schema primitives.

Reusable base models and generic containers to keep API schemas consistent and
DRY across the whole surface.
"""

from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class SchemaBase(BaseModel):
    """Base for all API schemas.

    ``from_attributes=True`` lets schemas be built directly from ORM objects,
    bridging the persistence and API layers without manual mapping.
    """

    model_config = ConfigDict(from_attributes=True)


class ResponseBase(SchemaBase):
    """Common fields returned by every entity response (DRY).

    Mirrors the columns provided by the ORM :class:`Entity` base so every
    ``*Response`` schema exposes identity, audit timestamps and soft-delete
    state consistently.
    """

    id: UUID
    created_at: datetime
    updated_at: datetime
    is_deleted: bool


class PaginationParams(SchemaBase):
    """Standard pagination query parameters."""

    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class Page(SchemaBase, Generic[T]):
    """Generic paginated response envelope."""

    items: list[T]
    total: int
    limit: int
    offset: int
