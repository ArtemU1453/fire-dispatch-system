"""Schemas for :class:`Organization`."""

from __future__ import annotations

from uuid import UUID

from app.schemas.catalog import (
    CatalogCreateBase,
    CatalogResponseBase,
    CatalogUpdateBase,
)


class OrganizationCreate(CatalogCreateBase):
    parent_id: UUID | None = None
    phone: str | None = None
    email: str | None = None


class OrganizationUpdate(CatalogUpdateBase):
    parent_id: UUID | None = None
    phone: str | None = None
    email: str | None = None


class OrganizationResponse(CatalogResponseBase):
    parent_id: UUID | None = None
    phone: str | None = None
    email: str | None = None
