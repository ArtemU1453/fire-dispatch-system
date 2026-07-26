"""ORM models for call management.

A **Call** is the record of an incoming (or outgoing) emergency call. Each call
becomes its own entity and is linked to one or more **incident** cards. Around
the call this module models the **queue** entry (multi-workstation dispatching),
an append-only **history**, **participants**, **recordings** and **transcripts**
(architecture only — no audio / ASR yet), the **incident links** and free-form
**metadata**.

All tables reuse the Stage-2 ``Entity`` base (UUID PK, timestamps, soft-delete)
and reference existing entities (``incidents`` from Stage 9, ``organizations``,
``users``) — nothing from earlier stages is modified.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.calls.models.enums import (
    CallDirection,
    CallEventType,
    CallLinkType,
    CallParticipantRole,
    CallPriority,
    CallQueueStatus,
    CallRecordingStatus,
    CallSource,
    CallStatus,
    CallTranscriptStatus,
    CallType,
)
from app.calls.models.types import (
    call_direction_enum,
    call_event_enum,
    call_link_type_enum,
    call_participant_role_enum,
    call_priority_enum,
    call_queue_status_enum,
    call_recording_status_enum,
    call_source_enum,
    call_status_enum,
    call_transcript_status_enum,
    call_type_enum,
)
from app.models.base import Entity

if TYPE_CHECKING:
    from app.incidents.models.entities import Incident
    from app.models.organization import Organization


class Call(Entity):
    """An emergency call — the central entity of this module."""

    __tablename__ = "calls"
    __table_args__ = (
        Index("ix_calls_status_created", "status", "created_at"),
    )

    number: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True
    )
    external_id: Mapped[str | None] = mapped_column(
        String(128), nullable=True, index=True
    )
    direction: Mapped[CallDirection] = mapped_column(
        call_direction_enum,
        server_default=CallDirection.INBOUND.value,
        nullable=False,
    )
    call_type: Mapped[CallType] = mapped_column(
        call_type_enum, server_default=CallType.EMERGENCY.value, nullable=False,
        index=True,
    )
    source: Mapped[CallSource] = mapped_column(
        call_source_enum, server_default=CallSource.PHONE.value, nullable=False,
    )
    status: Mapped[CallStatus] = mapped_column(
        call_status_enum, server_default=CallStatus.NEW.value, nullable=False,
        index=True,
    )
    priority: Mapped[CallPriority] = mapped_column(
        call_priority_enum, server_default=CallPriority.NORMAL.value,
        nullable=False, index=True,
    )
    caller_number: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )
    caller_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    callee_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    address_hint: Mapped[str | None] = mapped_column(String(512), nullable=True)
    dispatcher_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    dispatcher_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    incident_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    notes: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    answered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    wait_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    talk_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # The primary linked incident (convenience; full set via ``links``).
    incident: Mapped[Incident | None] = relationship("Incident", lazy="raise")

    queue_entry: Mapped[CallQueueEntry | None] = relationship(
        back_populates="call", cascade="all, delete-orphan", uselist=False
    )
    history: Mapped[list[CallHistory]] = relationship(
        back_populates="call", cascade="all, delete-orphan"
    )
    participants: Mapped[list[CallParticipant]] = relationship(
        back_populates="call", cascade="all, delete-orphan"
    )
    recordings: Mapped[list[CallRecording]] = relationship(
        back_populates="call", cascade="all, delete-orphan"
    )
    transcripts: Mapped[list[CallTranscript]] = relationship(
        back_populates="call", cascade="all, delete-orphan"
    )
    links: Mapped[list[CallIncidentLink]] = relationship(
        back_populates="call", cascade="all, delete-orphan"
    )
    call_metadata: Mapped[list[CallMetadata]] = relationship(
        back_populates="call", cascade="all, delete-orphan"
    )


class CallQueueEntry(Entity):
    """A call's position in the dispatch queue.

    The queue supports **priority**, arrival time, an assigned dispatcher /
    workstation and a status, so multiple dispatcher workstations can pull from
    the same queue.
    """

    __tablename__ = "call_queue"
    __table_args__ = (
        UniqueConstraint("call_id", name="uq_call_queue_call"),
        Index("ix_call_queue_status_priority", "status", "priority"),
    )

    call_id: Mapped[UUID] = mapped_column(
        ForeignKey("calls.id", ondelete="CASCADE"), nullable=False, index=True
    )
    priority: Mapped[CallPriority] = mapped_column(
        call_priority_enum, server_default=CallPriority.NORMAL.value,
        nullable=False,
    )
    status: Mapped[CallQueueStatus] = mapped_column(
        call_queue_status_enum, server_default=CallQueueStatus.WAITING.value,
        nullable=False, index=True,
    )
    enqueued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    assigned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    removed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    dispatcher_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    dispatcher_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    workstation: Mapped[str | None] = mapped_column(String(64), nullable=True)
    note: Mapped[str | None] = mapped_column(String(512), nullable=True)

    call: Mapped[Call] = relationship(back_populates="queue_entry")


class CallHistory(Entity):
    """Append-only history of a call's changes (never deleted).

    Captures status changes, queueing, dispatcher assignment, incident
    creation / linking and provider actions — with the actor, the source, the
    old → new status and the related incident.
    """

    __tablename__ = "call_history"
    __table_args__ = (
        Index("ix_call_history_call_time", "call_id", "occurred_at"),
        Index("ix_call_history_time", "occurred_at"),
    )

    call_id: Mapped[UUID] = mapped_column(
        ForeignKey("calls.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[CallEventType] = mapped_column(
        call_event_enum, nullable=False, index=True
    )
    from_status: Mapped[CallStatus | None] = mapped_column(
        call_status_enum, nullable=True
    )
    to_status: Mapped[CallStatus | None] = mapped_column(
        call_status_enum, nullable=True
    )
    changed_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    changed_by_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str] = mapped_column(
        String(32), server_default="dispatcher", nullable=False
    )
    incident_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True
    )
    detail: Mapped[str | None] = mapped_column(String(512), nullable=True)
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    call: Mapped[Call] = relationship(back_populates="history")


class CallParticipant(Entity):
    """A party involved in the call (caller, dispatcher, transfer target …)."""

    __tablename__ = "call_participants"

    call_id: Mapped[UUID] = mapped_column(
        ForeignKey("calls.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[CallParticipantRole] = mapped_column(
        call_participant_role_enum,
        server_default=CallParticipantRole.CALLER.value, nullable=False,
    )
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    organization_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(String(512), nullable=True)

    call: Mapped[Call] = relationship(back_populates="participants")
    organization: Mapped[Organization | None] = relationship(
        "Organization", lazy="raise"
    )


class CallRecording(Entity):
    """Metadata for a call recording — **architecture only** (no audio stored).

    Holds the external reference, duration, format, storage location and
    processing status so a real recording backend can be plugged in later.
    """

    __tablename__ = "call_recordings"

    call_id: Mapped[UUID] = mapped_column(
        ForeignKey("calls.id", ondelete="CASCADE"), nullable=False, index=True
    )
    external_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    audio_format: Mapped[str | None] = mapped_column(String(32), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    storage_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[CallRecordingStatus] = mapped_column(
        call_recording_status_enum,
        server_default=CallRecordingStatus.PENDING.value, nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    note: Mapped[str | None] = mapped_column(String(512), nullable=True)

    call: Mapped[Call] = relationship(back_populates="recordings")


class CallTranscript(Entity):
    """A transcript of the call — **architecture only** (no ASR yet).

    Stores the source text, temporal segments (as JSONB), the language and the
    processing status so an automatic speech-recognition engine can populate it
    later.
    """

    __tablename__ = "call_transcripts"

    call_id: Mapped[UUID] = mapped_column(
        ForeignKey("calls.id", ondelete="CASCADE"), nullable=False, index=True
    )
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    text_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    segments: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[CallTranscriptStatus] = mapped_column(
        call_transcript_status_enum,
        server_default=CallTranscriptStatus.PENDING.value, nullable=False,
    )
    engine: Mapped[str | None] = mapped_column(String(64), nullable=True)
    note: Mapped[str | None] = mapped_column(String(512), nullable=True)

    call: Mapped[Call] = relationship(back_populates="transcripts")


class CallIncidentLink(Entity):
    """A link between a call and an incident card.

    A call typically creates a new incident, but can also be attached to an
    existing one. ``link_type`` distinguishes the two; ``is_primary`` marks the
    main incident for the call.
    """

    __tablename__ = "call_incident_links"
    __table_args__ = (
        UniqueConstraint("call_id", "incident_id", name="uq_call_incident_link"),
    )

    call_id: Mapped[UUID] = mapped_column(
        ForeignKey("calls.id", ondelete="CASCADE"), nullable=False, index=True
    )
    incident_id: Mapped[UUID] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    link_type: Mapped[CallLinkType] = mapped_column(
        call_link_type_enum, server_default=CallLinkType.LINKED.value,
        nullable=False,
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    note: Mapped[str | None] = mapped_column(String(512), nullable=True)

    call: Mapped[Call] = relationship(back_populates="links")
    incident: Mapped[Incident] = relationship("Incident", lazy="raise")


class CallMetadata(Entity):
    """Free-form key/value metadata attached to a call (extension seam)."""

    __tablename__ = "call_metadata"
    __table_args__ = (
        UniqueConstraint("call_id", "key", name="uq_call_metadata_key"),
    )

    call_id: Mapped[UUID] = mapped_column(
        ForeignKey("calls.id", ondelete="CASCADE"), nullable=False, index=True
    )
    key: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    call: Mapped[Call] = relationship(back_populates="call_metadata")
