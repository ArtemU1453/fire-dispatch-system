"""Core resource model — the universal unit of the system.

Every physical or logical asset the dispatcher works with is a ``Resource``:
stations, vehicles, personnel, equipment, hydrants, water sources, hospitals,
police units, gas/power services, warehouses and command posts. What a resource
*is* comes from its :class:`ResourceType` (a catalog row), so new kinds of asset
are added as data. Structured, type-specific attributes live in optional 1:1
specialization tables (:class:`Station`, :class:`Vehicle`, :class:`Personnel`,
:class:`Equipment`) — never in JSON — keeping the schema in 3NF.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Entity
from app.models.mixins import GeoPointMixin

if TYPE_CHECKING:
    from app.models.assets import Equipment, Personnel, Station, Vehicle
    from app.models.catalog import AvailabilityStatus, Capability, ResourceType
    from app.models.geo import CoverageArea, Location
    from app.models.history import CoordinateHistory, StatusHistory
    from app.models.organization import Organization


class Resource(Entity, GeoPointMixin):
    """A dispatchable/manageable asset of any kind."""

    __tablename__ = "resources"
    __table_args__ = (
        UniqueConstraint("code", name="uq_resources_code"),
        # Hot path: find active resources of a type/org by status.
        Index(
            "ix_resources_active",
            "organization_id",
            "resource_type_id",
            "availability_status_id",
            postgresql_where=text("is_deleted = false"),
        ),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), nullable=False
    )

    resource_type_id: Mapped[UUID] = mapped_column(
        ForeignKey("resource_types.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    availability_status_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("availability_statuses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    location_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("locations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Self-referential: the station resource (category STATION) this asset is
    # based at. Kept self-referential to avoid a circular table dependency.
    home_station_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("resources.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # --- relationships ----------------------------------------------------
    resource_type: Mapped[ResourceType] = relationship(back_populates="resources")
    organization: Mapped[Organization] = relationship(back_populates="resources")
    availability_status: Mapped[AvailabilityStatus | None] = relationship()
    location: Mapped[Location | None] = relationship(back_populates="resources")
    home_station: Mapped[Resource | None] = relationship(
        remote_side="Resource.id"
    )

    capability_links: Mapped[list[ResourceCapability]] = relationship(
        back_populates="resource", cascade="all, delete-orphan"
    )
    status_history: Mapped[list[StatusHistory]] = relationship(
        back_populates="resource", cascade="all, delete-orphan"
    )
    coordinate_history: Mapped[list[CoordinateHistory]] = relationship(
        back_populates="resource", cascade="all, delete-orphan"
    )
    coverage_areas: Mapped[list[CoverageArea]] = relationship(
        back_populates="resource"
    )

    # 1:1 specializations (present only for the matching category).
    station: Mapped[Station | None] = relationship(
        back_populates="resource", uselist=False, cascade="all, delete-orphan"
    )
    vehicle: Mapped[Vehicle | None] = relationship(
        back_populates="resource", uselist=False, cascade="all, delete-orphan"
    )
    personnel: Mapped[Personnel | None] = relationship(
        back_populates="resource", uselist=False, cascade="all, delete-orphan"
    )
    equipment: Mapped[Equipment | None] = relationship(
        back_populates="resource", uselist=False, cascade="all, delete-orphan"
    )


class ResourceCapability(Entity):
    """Junction: capabilities a :class:`Resource` provides, with quantity."""

    __tablename__ = "resource_capabilities"
    __table_args__ = (
        UniqueConstraint(
            "resource_id", "capability_id", name="uq_resource_capability"
        ),
    )

    resource_id: Mapped[UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    capability_id: Mapped[UUID] = mapped_column(
        ForeignKey("capabilities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, server_default="1", nullable=False)

    resource: Mapped[Resource] = relationship(back_populates="capability_links")
    capability: Mapped[Capability] = relationship(back_populates="resource_links")
