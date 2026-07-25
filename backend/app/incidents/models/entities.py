"""ORM models for incident management.

The **Incident** is the central entity of the whole system: every other
subsystem (GIS, Search, Rules, Dispatch, Routing, Recommendation) is related to
an incident. An incident owns its **locations**, **participants**, **comments**,
**attachments** (metadata only at this stage), a **timeline** (chronology), a
field-level **history** (audit), linked **recommendations** and **dispatched
units**, and a technical **log**.

All tables reuse the Stage-2 ``Entity`` base (UUID PK, timestamps, soft-delete)
and reference existing catalogs (incident types, administrative areas,
organizations, resources, dispatch recommendations) — nothing from earlier stages
is modified.
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
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.incidents.models.enums import (
    AttachmentKind,
    ChangeSource,
    DispatchUnitStatus,
    IncidentCategory,
    IncidentPriority,
    IncidentSource,
    IncidentStatus,
    TimelineEventType,
)
from app.incidents.models.types import (
    attachment_kind_enum,
    change_source_enum,
    dispatch_unit_status_enum,
    incident_category_enum,
    incident_priority_enum,
    incident_source_enum,
    incident_status_enum,
    timeline_event_enum,
)
from app.models.base import Entity


class Incident(Entity):
    """The central incident card."""

    __tablename__ = "incidents"
    __table_args__ = (
        Index("ix_incidents_status_created", "status", "created_at"),
    )

    number: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True
    )
    incident_type_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("incident_types.id", ondelete="SET NULL"), nullable=True, index=True
    )
    category: Mapped[IncidentCategory] = mapped_column(
        incident_category_enum,
        server_default=IncidentCategory.OTHER.value,
        nullable=False,
        index=True,
    )
    source: Mapped[IncidentSource] = mapped_column(
        incident_source_enum,
        server_default=IncidentSource.PHONE.value,
        nullable=False,
    )
    status: Mapped[IncidentStatus] = mapped_column(
        incident_status_enum,
        server_default=IncidentStatus.CREATED.value,
        nullable=False,
        index=True,
    )
    priority: Mapped[IncidentPriority] = mapped_column(
        incident_priority_enum,
        server_default=IncidentPriority.NORMAL.value,
        nullable=False,
        index=True,
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(String(4096), nullable=True)

    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    administrative_area_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("administrative_areas.id", ondelete="SET NULL"), nullable=True
    )
    danger_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    object_type: Mapped[str | None] = mapped_column(String(128), nullable=True)

    reporter_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reporter_contact: Mapped[str | None] = mapped_column(String(128), nullable=True)

    reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    locations: Mapped[list[IncidentLocation]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )
    participants: Mapped[list[IncidentParticipant]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )
    comments: Mapped[list[IncidentComment]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )
    attachments: Mapped[list[IncidentAttachment]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )
    timeline: Mapped[list[IncidentTimeline]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )
    history: Mapped[list[IncidentHistory]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )
    recommendations: Mapped[list[IncidentRecommendation]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )
    dispatches: Mapped[list[IncidentDispatch]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )
    logs: Mapped[list[IncidentLog]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )


class IncidentLocation(Entity):
    """A (possibly geocoded) location record for an incident."""

    __tablename__ = "incident_locations"

    incident_id: Mapped[UUID] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    administrative_area_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("administrative_areas.id", ondelete="SET NULL"), nullable=True
    )
    accuracy: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_primary: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    note: Mapped[str | None] = mapped_column(String(512), nullable=True)

    incident: Mapped[Incident] = relationship(back_populates="locations")


class IncidentParticipant(Entity):
    """A participant related to an incident (reporter, victim, responder, …)."""

    __tablename__ = "incident_participants"

    incident_id: Mapped[UUID] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact: Mapped[str | None] = mapped_column(String(128), nullable=True)
    organization_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(String(512), nullable=True)

    incident: Mapped[Incident] = relationship(back_populates="participants")


class IncidentComment(Entity):
    """A dispatcher comment on an incident (kept in the history/timeline too)."""

    __tablename__ = "incident_comments"

    incident_id: Mapped[UUID] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    author_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    text: Mapped[str] = mapped_column(String(4096), nullable=False)

    incident: Mapped[Incident] = relationship(back_populates="comments")


class IncidentAttachment(Entity):
    """Attachment **metadata** (architecture only — no binary storage yet)."""

    __tablename__ = "incident_attachments"

    incident_id: Mapped[UUID] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[AttachmentKind] = mapped_column(
        attachment_kind_enum,
        server_default=AttachmentKind.OTHER.value,
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    storage_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    uploaded_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    incident: Mapped[Incident] = relationship(back_populates="attachments")


class IncidentTimeline(Entity):
    """A chronology entry — the human-facing sequence of what happened."""

    __tablename__ = "incident_timeline"
    __table_args__ = (
        Index("ix_incident_timeline_incident_time", "incident_id", "occurred_at"),
    )

    incident_id: Mapped[UUID] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[TimelineEventType] = mapped_column(
        timeline_event_enum, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    detail: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    actor_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    actor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    incident: Mapped[Incident] = relationship(back_populates="timeline")


class IncidentHistory(Entity):
    """A field-level change record (old → new) for the audit trail."""

    __tablename__ = "incident_history"
    __table_args__ = (
        Index("ix_incident_history_incident_time", "incident_id", "occurred_at"),
    )

    incident_id: Mapped[UUID] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    field: Mapped[str] = mapped_column(String(64), nullable=False)
    old_value: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    new_value: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    change_source: Mapped[ChangeSource] = mapped_column(
        change_source_enum,
        server_default=ChangeSource.DISPATCHER.value,
        nullable=False,
    )
    changed_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    changed_by_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note: Mapped[str | None] = mapped_column(String(512), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    incident: Mapped[Incident] = relationship(back_populates="history")


class IncidentRecommendation(Entity):
    """Link between an incident and a dispatch recommendation (Dispatch Engine)."""

    __tablename__ = "incident_recommendations"

    incident_id: Mapped[UUID] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recommendation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("dispatch_recommendations.id", ondelete="SET NULL"), nullable=True
    )
    is_current: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), nullable=False
    )
    note: Mapped[str | None] = mapped_column(String(512), nullable=True)

    incident: Mapped[Incident] = relationship(back_populates="recommendations")


class IncidentDispatch(Entity):
    """A unit assigned / dispatched to an incident (references a resource)."""

    __tablename__ = "incident_dispatches"
    __table_args__ = (
        UniqueConstraint("incident_id", "resource_id", name="uq_incident_dispatch"),
    )

    incident_id: Mapped[UUID] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resource_id: Mapped[UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(
        String(32), server_default="primary", nullable=False
    )
    status: Mapped[DispatchUnitStatus] = mapped_column(
        dispatch_unit_status_enum,
        server_default=DispatchUnitStatus.ASSIGNED.value,
        nullable=False,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    note: Mapped[str | None] = mapped_column(String(512), nullable=True)

    incident: Mapped[Incident] = relationship(back_populates="dispatches")


class IncidentLog(Entity):
    """A technical/system log entry for an incident (distinct from the timeline)."""

    __tablename__ = "incident_logs"
    __table_args__ = (
        Index("ix_incident_logs_incident_time", "incident_id", "occurred_at"),
    )

    incident_id: Mapped[UUID] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    level: Mapped[str] = mapped_column(
        String(16), server_default="info", nullable=False
    )
    actor_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    incident: Mapped[Incident] = relationship(back_populates="logs")
