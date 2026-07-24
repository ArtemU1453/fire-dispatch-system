"""Time-series history tables (high-volume).

- :class:`StatusHistory` — every availability-status transition of a resource.
- :class:`CoordinateHistory` — GPS track points of mobile resources.

Both are expected to hold millions of rows. They are indexed on
``(resource_id, <time> DESC)`` for fast "latest / recent" lookups and are
designed to be range-partitioned by time (see the recommendations in
``docs/data-model.md``). ``CoordinateHistory`` also carries a GiST-indexed point.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from geoalchemy2 import Geometry
from geoalchemy2.elements import WKBElement
from sqlalchemy import DateTime, Float, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Entity
from app.models.mixins import SRID

if TYPE_CHECKING:
    from app.models.catalog import AvailabilityStatus
    from app.models.resource import Resource
    from app.models.security import User


class StatusHistory(Entity):
    """A single availability-status transition of a resource."""

    __tablename__ = "status_history"
    __table_args__ = (
        Index("ix_status_history_resource_time", "resource_id", "changed_at"),
    )

    resource_id: Mapped[UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_status_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("availability_statuses.id", ondelete="SET NULL"), nullable=True
    )
    to_status_id: Mapped[UUID] = mapped_column(
        ForeignKey("availability_statuses.id", ondelete="RESTRICT"), nullable=False
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    changed_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reason: Mapped[str | None] = mapped_column(String(512), nullable=True)

    resource: Mapped[Resource] = relationship(back_populates="status_history")
    from_status: Mapped[AvailabilityStatus | None] = relationship(
        foreign_keys=[from_status_id]
    )
    to_status: Mapped[AvailabilityStatus] = relationship(foreign_keys=[to_status_id])
    changed_by: Mapped[User | None] = relationship()


class CoordinateHistory(Entity):
    """A single GPS track point for a mobile resource."""

    __tablename__ = "coordinate_history"
    __table_args__ = (
        Index("ix_coordinate_history_resource_time", "resource_id", "recorded_at"),
    )

    resource_id: Mapped[UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    geom: Mapped[WKBElement | None] = mapped_column(
        Geometry(geometry_type="POINT", srid=SRID, spatial_index=True),
        nullable=True,
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    speed_kmh: Mapped[float | None] = mapped_column(Float, nullable=True)
    heading_deg: Mapped[float | None] = mapped_column(Float, nullable=True)
    accuracy_m: Mapped[float | None] = mapped_column(Float, nullable=True)

    resource: Mapped[Resource] = relationship(back_populates="coordinate_history")
