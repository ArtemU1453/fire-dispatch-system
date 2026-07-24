"""SQLAlchemy declarative base.

A single ``Base`` shared by every ORM model. Kept separate from the engine /
session module so that Alembic and the models can import metadata without
pulling in engine construction (avoids import cycles).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


class TimestampMixin:
    """Reusable ``created_at`` / ``updated_at`` columns (DRY).

    Any model can inherit this to get audit timestamps managed by the database.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
