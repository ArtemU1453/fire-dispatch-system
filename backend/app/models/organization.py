"""Organization model — the owner/operator of resources.

Examples: an МЧС garrison, a municipal hospital network, a police department,
a gas utility. Self-referential to represent organizational hierarchy.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import CatalogEntity

if TYPE_CHECKING:
    from app.models.resource import Resource


class Organization(CatalogEntity):
    """An organization that owns and operates resources."""

    __tablename__ = "organizations"

    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    parent: Mapped[Organization | None] = relationship(
        remote_side="Organization.id", back_populates="children"
    )
    children: Mapped[list[Organization]] = relationship(back_populates="parent")
    resources: Mapped[list[Resource]] = relationship(back_populates="organization")
