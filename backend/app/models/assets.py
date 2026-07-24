"""Resource specialization tables (1:1 with :class:`Resource`).

These hold structured, type-specific attributes for the four asset families that
have rich, queryable fields. Each row extends exactly one resource via a unique
``resource_id`` (class-table inheritance without polymorphic magic — explicit and
migration-friendly). Assets that need no extra columns (hydrants, hospitals, …)
remain plain resources distinguished only by their :class:`ResourceType`.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Entity

if TYPE_CHECKING:
    from app.models.catalog import EquipmentType, PersonnelRole, VehicleType
    from app.models.resource import Resource


class Station(Entity):
    """Fire station / depot specifics."""

    __tablename__ = "stations"

    resource_id: Mapped[UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    station_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    garage_capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    staff_capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_round_the_clock: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), nullable=False
    )

    resource: Mapped[Resource] = relationship(back_populates="station")


class Vehicle(Entity):
    """Apparatus / vehicle specifics (typed by :class:`VehicleType`)."""

    __tablename__ = "vehicles"

    resource_id: Mapped[UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    vehicle_type_id: Mapped[UUID] = mapped_column(
        ForeignKey("vehicle_types.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    plate_number: Mapped[str | None] = mapped_column(
        String(32), nullable=True, unique=True
    )
    crew_capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    water_capacity_l: Mapped[int | None] = mapped_column(Integer, nullable=True)
    foam_capacity_l: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pump_capacity_l_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ladder_height_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    year_manufactured: Mapped[int | None] = mapped_column(Integer, nullable=True)
    odometer_km: Mapped[int | None] = mapped_column(Integer, nullable=True)

    resource: Mapped[Resource] = relationship(back_populates="vehicle")
    vehicle_type: Mapped[VehicleType] = relationship(back_populates="vehicles")


class Personnel(Entity):
    """Person / crew-member specifics (typed by :class:`PersonnelRole`)."""

    __tablename__ = "personnel"

    resource_id: Mapped[UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    personnel_role_id: Mapped[UUID] = mapped_column(
        ForeignKey("personnel_roles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    last_name: Mapped[str] = mapped_column(String(128), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    rank: Mapped[str | None] = mapped_column(String(64), nullable=True)
    badge_number: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True
    )
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hired_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    resource: Mapped[Resource] = relationship(back_populates="personnel")
    role: Mapped[PersonnelRole] = relationship(back_populates="personnel")


class Equipment(Entity):
    """Equipment / gear specifics (typed by :class:`EquipmentType`)."""

    __tablename__ = "equipment"

    resource_id: Mapped[UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    equipment_type_id: Mapped[UUID] = mapped_column(
        ForeignKey("equipment_types.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    serial_number: Mapped[str | None] = mapped_column(
        String(128), nullable=True, unique=True
    )
    inventory_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, server_default="1", nullable=False)
    last_service_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    resource: Mapped[Resource] = relationship(back_populates="equipment")
    equipment_type: Mapped[EquipmentType] = relationship(back_populates="equipment")
