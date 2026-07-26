"""ORM models for real-time resource / unit management.

This module adds the *operational* concepts on top of the Stage-2 resource data
model (which it never modifies): **units** (dispatchable подразделения),
**crews** and their **members**, **shifts** and **duty rosters**, **assignments**
to incidents, per-vehicle **operational state**, personnel **qualifications**, and
an append-only **management history**.

Statuses are the Stage-2 ``availability_statuses`` catalog (data, not code).
Vehicles / personnel / stations are the existing ``resources`` and their sub-type
rows — referenced by id, never redefined.
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Time,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Entity
from app.resources.models.enums import (
    AssignmentStatus,
    QualificationKind,
    ResourceEventType,
    TechnicalCondition,
)
from app.resources.models.types import (
    assignment_status_enum,
    qualification_kind_enum,
    resource_event_enum,
    technical_condition_enum,
)

if TYPE_CHECKING:
    from app.models.catalog import AvailabilityStatus
    from app.models.organization import Organization
    from app.models.resource import Resource, Station


class Unit(Entity):
    """A dispatchable operational unit (отделение / расчёт).

    Ties a station, a vehicle (a Stage-2 resource) and its crews together, and
    carries its own current status (from the shared availability catalog).
    """

    __tablename__ = "units"

    code: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    call_sign: Mapped[str | None] = mapped_column(String(64), nullable=True)
    station_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("stations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    organization_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    vehicle_resource_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("resources.id", ondelete="SET NULL"), nullable=True, index=True
    )
    availability_status_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("availability_statuses.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), nullable=False, index=True
    )
    notes: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    station: Mapped[Station | None] = relationship("Station", lazy="raise")
    organization: Mapped[Organization | None] = relationship(
        "Organization", lazy="raise"
    )
    vehicle: Mapped[Resource | None] = relationship(
        "Resource", foreign_keys=[vehicle_resource_id], lazy="raise"
    )
    availability_status: Mapped[AvailabilityStatus | None] = relationship(
        "AvailabilityStatus", lazy="raise"
    )
    crews: Mapped[list[Crew]] = relationship(
        back_populates="unit", cascade="all, delete-orphan"
    )
    assignments: Mapped[list[ResourceAssignment]] = relationship(
        back_populates="unit", cascade="all, delete-orphan"
    )


class Shift(Entity):
    """A duty shift template (смена)."""

    __tablename__ = "shifts"

    code: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    rotation: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), nullable=False
    )


class Crew(Entity):
    """A crew (караул / экипаж) — the people currently manning a unit."""

    __tablename__ = "crews"

    code: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("units.id", ondelete="SET NULL"), nullable=True, index=True
    )
    shift_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("shifts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    organization_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    is_on_duty: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    unit: Mapped[Unit | None] = relationship(back_populates="crews")
    shift: Mapped[Shift | None] = relationship("Shift", lazy="raise")
    members: Mapped[list[CrewMember]] = relationship(
        back_populates="crew", cascade="all, delete-orphan"
    )


class CrewMember(Entity):
    """A person on a crew (references a Stage-2 personnel resource)."""

    __tablename__ = "crew_members"
    __table_args__ = (
        UniqueConstraint(
            "crew_id", "personnel_resource_id", name="uq_crew_member"
        ),
    )

    crew_id: Mapped[UUID] = mapped_column(
        ForeignKey("crews.id", ondelete="CASCADE"), nullable=False, index=True
    )
    personnel_resource_id: Mapped[UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_commander: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    left_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    crew: Mapped[Crew] = relationship(back_populates="members")
    personnel: Mapped[Resource] = relationship(
        "Resource", foreign_keys=[personnel_resource_id], lazy="raise"
    )


class DutyRoster(Entity):
    """A duty-roster entry: which crew mans which shift on a date."""

    __tablename__ = "duty_rosters"
    __table_args__ = (
        UniqueConstraint(
            "roster_date", "shift_id", "crew_id", name="uq_duty_roster"
        ),
    )

    roster_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    shift_id: Mapped[UUID] = mapped_column(
        ForeignKey("shifts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    crew_id: Mapped[UUID] = mapped_column(
        ForeignKey("crews.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unit_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("units.id", ondelete="SET NULL"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(String(512), nullable=True)


class ResourceAssignment(Entity):
    """A unit's assignment to an incident (the resource-management view)."""

    __tablename__ = "resource_assignments"
    __table_args__ = (
        Index("ix_resource_assignments_unit_status", "unit_id", "status"),
    )

    unit_id: Mapped[UUID] = mapped_column(
        ForeignKey("units.id", ondelete="CASCADE"), nullable=False, index=True
    )
    incident_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    role: Mapped[str] = mapped_column(
        String(32), server_default="primary", nullable=False
    )
    status: Mapped[AssignmentStatus] = mapped_column(
        assignment_status_enum,
        server_default=AssignmentStatus.ACTIVE.value,
        nullable=False,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    released_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    note: Mapped[str | None] = mapped_column(String(512), nullable=True)

    unit: Mapped[Unit] = relationship(back_populates="assignments")


class VehicleState(Entity):
    """Per-vehicle operational state (fuel, mileage, condition, service).

    Extends the Stage-2 ``vehicles`` row (keyed by its resource id) without
    modifying it.
    """

    __tablename__ = "vehicle_states"
    __table_args__ = (
        UniqueConstraint("vehicle_resource_id", name="uq_vehicle_state"),
    )

    vehicle_resource_id: Mapped[UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fuel_level_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mileage_km: Mapped[int | None] = mapped_column(Integer, nullable=True)
    technical_condition: Mapped[TechnicalCondition] = mapped_column(
        technical_condition_enum,
        server_default=TechnicalCondition.OPERATIONAL.value,
        nullable=False,
    )
    last_service_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_service_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_available: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), nullable=False
    )
    note: Mapped[str | None] = mapped_column(String(512), nullable=True)


class PersonnelQualification(Entity):
    """A personnel qualification / clearance / (future) medical restriction."""

    __tablename__ = "personnel_qualifications"

    personnel_resource_id: Mapped[UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[QualificationKind] = mapped_column(
        qualification_kind_enum,
        server_default=QualificationKind.QUALIFICATION.value,
        nullable=False,
    )
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    note: Mapped[str | None] = mapped_column(String(512), nullable=True)


class ResourceManagementHistory(Entity):
    """Append-only history of resource / unit / crew changes (never deleted).

    Captures status changes, crew changes, and incident assignment / return —
    with the actor, the source, the old / new value and the related incident.
    """

    __tablename__ = "resource_management_history"
    __table_args__ = (
        Index("ix_resource_history_time", "occurred_at"),
        Index("ix_resource_history_resource", "resource_id", "occurred_at"),
        Index("ix_resource_history_unit", "unit_id", "occurred_at"),
    )

    resource_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("resources.id", ondelete="SET NULL"), nullable=True
    )
    unit_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("units.id", ondelete="SET NULL"), nullable=True
    )
    crew_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("crews.id", ondelete="SET NULL"), nullable=True
    )
    event_type: Mapped[ResourceEventType] = mapped_column(
        resource_event_enum, nullable=False, index=True
    )
    from_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    to_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    changed_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    changed_by_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str] = mapped_column(
        String(32), server_default="dispatcher", nullable=False
    )
    incident_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
