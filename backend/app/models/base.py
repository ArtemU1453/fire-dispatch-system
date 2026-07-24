"""Reusable ORM model primitives.

Provides an ``IdentifiableBase`` combining a surrogate primary key with audit
timestamps. Concrete domain models (added later) should inherit from it so the
table shape stays consistent across the schema without repetition (DRY).
"""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import UUID as SA_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class IdentifiableBase(Base, TimestampMixin):
    """Abstract base with a UUID primary key and audit timestamps.

    Declared abstract so SQLAlchemy does not create a table for it directly.
    """

    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        SA_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
