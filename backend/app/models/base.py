"""Reusable ORM model primitives.

Provides ``Entity`` — the common base for every domain model — combining a UUID
surrogate primary key, audit timestamps (``created_at`` / ``updated_at``) and a
soft-delete flag (``is_deleted``). Concrete models inherit from it so the table
shape stays consistent across the whole schema without repetition (DRY).
"""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import UUID as SA_UUID
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, SoftDeleteMixin, TimestampMixin


class Entity(Base, TimestampMixin, SoftDeleteMixin):
    """Abstract base with UUID PK, audit timestamps and soft-delete flag.

    Declared abstract so SQLAlchemy does not create a table for it directly.
    """

    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        SA_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )


class CatalogEntity(Entity):
    """Base for lookup / catalog tables that share a ``code`` + ``name`` shape.

    Catalog tables (types, roles, statuses) are the extension mechanism of the
    system: new categories are added as **rows**, never as schema changes. A
    stable unique ``code`` is used by application logic; ``name`` is the
    human-readable label.
    """

    __abstract__ = True

    code: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
