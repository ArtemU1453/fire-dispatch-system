"""ORM models for the Crisis Management Platform (Stage 20).

An overlay schema (all tables prefixed ``crisis_``) for large-scale emergency
operations. It references existing data (incidents, units, users) **by id only**
— no foreign keys into other modules' tables — so it never modifies or couples
to the base system. Status/type fields are stored as plain ``String`` values
(validated by the app-level enums in ``enums.py``); response *levels* live in a
configurable reference table so they change without code.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.crisis.models.enums import (
    JournalKind,
    OperationStatus,
    SectorStatus,
    StageStatus,
    TaskStatus,
    ZoneKind,
)
from app.models.base import CatalogEntity, Entity


class CrisisResponseLevel(CatalogEntity):
    """Configurable response level (§3) — a справочник row, not an enum."""

    __tablename__ = "crisis_response_levels"

    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )


class EmergencyOperation(Entity):
    """A large-scale emergency operation / crisis (§2)."""

    __tablename__ = "crisis_operations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=OperationStatus.PLANNED.value
    )
    response_level_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("crisis_response_levels.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Loose reference to an existing incident (no FK — the base system is not
    # modified or hard-coupled).
    incident_ref: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class OperationalHeadquarters(Entity):
    """The operational headquarters of an operation (§4). One per operation."""

    __tablename__ = "crisis_headquarters"

    operation_id: Mapped[UUID] = mapped_column(
        ForeignKey("crisis_operations.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class CommandAssignment(Entity):
    """A commander or deputy assigned to the headquarters (§4)."""

    __tablename__ = "crisis_command_assignments"

    headquarters_id: Mapped[UUID] = mapped_column(
        ForeignKey("crisis_headquarters.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    user_ref: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    responsibilities: Mapped[str | None] = mapped_column(Text, nullable=True)


class OperationalSector(Entity):
    """An operational sector / участок of the scene (§5)."""

    __tablename__ = "crisis_sectors"

    operation_id: Mapped[UUID] = mapped_column(
        ForeignKey("crisis_operations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    leader_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=SectorStatus.FORMING.value
    )
    situation: Mapped[str | None] = mapped_column(Text, nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    center_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    center_lon: Mapped[float | None] = mapped_column(Float, nullable=True)


class OperationalZone(Entity):
    """A geographic operational zone for the situation board (§9)."""

    __tablename__ = "crisis_zones"

    operation_id: Mapped[UUID] = mapped_column(
        ForeignKey("crisis_operations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    sector_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("crisis_sectors.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(
        String(16), nullable=False, default=ZoneKind.HOT.value
    )
    center_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    center_lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    radius_m: Mapped[float | None] = mapped_column(Float, nullable=True)


class ResourceGroup(Entity):
    """A grouping of forces & means (§6)."""

    __tablename__ = "crisis_resource_groups"

    operation_id: Mapped[UUID] = mapped_column(
        ForeignKey("crisis_operations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    sector_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("crisis_sectors.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[str | None] = mapped_column(String(255), nullable=True)


class ResourceGroupMember(Entity):
    """A unit / vehicle / person assigned to a resource group (§6)."""

    __tablename__ = "crisis_resource_group_members"

    group_id: Mapped[UUID] = mapped_column(
        ForeignKey("crisis_resource_groups.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    ref: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)


class ResourceMove(Entity):
    """History of a group's relocation between sectors (§6)."""

    __tablename__ = "crisis_resource_moves"

    group_id: Mapped[UUID] = mapped_column(
        ForeignKey("crisis_resource_groups.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    from_sector_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("crisis_sectors.id", ondelete="SET NULL"), nullable=True
    )
    to_sector_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("crisis_sectors.id", ondelete="SET NULL"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(String(512), nullable=True)


class PlanStage(Entity):
    """A stage / phase of the operational plan (§7)."""

    __tablename__ = "crisis_plan_stages"

    operation_id: Mapped[UUID] = mapped_column(
        ForeignKey("crisis_operations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=StageStatus.PLANNED.value
    )


class OperationalTask(Entity):
    """A task within the operational plan (§7)."""

    __tablename__ = "crisis_tasks"

    operation_id: Mapped[UUID] = mapped_column(
        ForeignKey("crisis_operations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    stage_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("crisis_plan_stages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    sector_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("crisis_sectors.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    assignee_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=TaskStatus.PENDING.value
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class SituationReport(Entity):
    """A situation report snapshot (§2, §9)."""

    __tablename__ = "crisis_situation_reports"

    operation_id: Mapped[UUID] = mapped_column(
        ForeignKey("crisis_operations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    author_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class OperationalOrder(Entity):
    """An operational order issued during the operation (§2)."""

    __tablename__ = "crisis_operational_orders"

    operation_id: Mapped[UUID] = mapped_column(
        ForeignKey("crisis_operations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    number: Mapped[str] = mapped_column(String(64), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    issued_by_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)


class JournalEntry(Entity):
    """Unified, append-only operational journal (§8).

    Combines the action log and the decision log (``kind`` discriminates). The
    service layer only ever appends — entries are never updated or deleted, so
    the journal is immutable.
    """

    __tablename__ = "crisis_journal_entries"

    operation_id: Mapped[UUID] = mapped_column(
        ForeignKey("crisis_operations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True, default=JournalKind.ACTION.value
    )
    actor_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
