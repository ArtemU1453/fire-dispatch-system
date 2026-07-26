"""Pydantic schemas for call management."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

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
from app.incidents.models.enums import IncidentCategory, IncidentPriority
from app.schemas.common import ResponseBase, SchemaBase


# ------------------------------------------------------------------ inputs ---
class CallCreate(SchemaBase):
    """Register a new (incoming) call."""

    direction: CallDirection = CallDirection.INBOUND
    call_type: CallType = CallType.EMERGENCY
    source: CallSource = CallSource.PHONE
    priority: CallPriority = CallPriority.NORMAL
    caller_number: str | None = None
    caller_name: str | None = None
    callee_number: str | None = None
    address_hint: str | None = None
    notes: str | None = None
    external_id: str | None = None
    register_with_provider: bool = False
    actor_name: str | None = None


class CallUpdate(SchemaBase):
    """Change the status of a call (and optionally leave a note)."""

    status: CallStatus
    note: str | None = None
    actor_name: str | None = None


class AssignDispatcherRequest(SchemaBase):
    dispatcher_user_id: UUID | None = None
    dispatcher_name: str | None = None
    workstation: str | None = None
    actor_name: str | None = None


class LinkIncidentRequest(SchemaBase):
    """Attach a call to an incident: link an existing one or create a new one.

    Provide ``incident_id`` to link an existing card, or set ``create=true`` to
    create a new one from the call (optionally with an incident type, category,
    priority and location). Exactly one of the two must be chosen.
    """

    incident_id: UUID | None = None
    create: bool = False
    incident_type_id: UUID | None = None
    category: IncidentCategory = IncidentCategory.OTHER
    priority: IncidentPriority = IncidentPriority.NORMAL
    title: str | None = None
    description: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    actor_name: str | None = None


class TransferCallRequest(SchemaBase):
    destination: str
    actor_name: str | None = None


class ActorRequest(SchemaBase):
    actor_name: str | None = None


# --------------------------------------------------------------- responses ---
class CallQueueResponse(ResponseBase):
    call_id: UUID
    priority: CallPriority
    status: CallQueueStatus
    enqueued_at: datetime
    assigned_at: datetime | None = None
    removed_at: datetime | None = None
    dispatcher_user_id: UUID | None = None
    dispatcher_name: str | None = None
    workstation: str | None = None
    wait_seconds: int
    # Present on the queue listing (denormalized for the dispatcher board).
    call_number: str | None = None
    caller_number: str | None = None
    call_status: CallStatus | None = None


class CallParticipantResponse(ResponseBase):
    role: CallParticipantRole
    name: str | None = None
    phone_number: str | None = None
    organization_id: UUID | None = None
    note: str | None = None


class CallRecordingResponse(ResponseBase):
    external_ref: str | None = None
    audio_format: str | None = None
    duration_seconds: int | None = None
    storage_ref: str | None = None
    status: CallRecordingStatus
    started_at: datetime | None = None


class CallTranscriptResponse(ResponseBase):
    language: str | None = None
    text_content: str | None = None
    segments: dict[str, Any] | None = None
    status: CallTranscriptStatus
    engine: str | None = None


class CallIncidentLinkResponse(ResponseBase):
    incident_id: UUID
    link_type: CallLinkType
    is_primary: bool
    note: str | None = None


class CallHistoryResponse(ResponseBase):
    event_type: CallEventType
    from_status: CallStatus | None = None
    to_status: CallStatus | None = None
    changed_by_name: str | None = None
    source: str
    incident_id: UUID | None = None
    detail: str | None = None
    meta: dict[str, Any] | None = None
    occurred_at: datetime


class CallResponse(ResponseBase):
    number: str
    external_id: str | None = None
    direction: CallDirection
    call_type: CallType
    source: CallSource
    status: CallStatus
    priority: CallPriority
    caller_number: str | None = None
    caller_name: str | None = None
    callee_number: str | None = None
    address_hint: str | None = None
    dispatcher_user_id: UUID | None = None
    dispatcher_name: str | None = None
    incident_id: UUID | None = None
    notes: str | None = None
    received_at: datetime
    answered_at: datetime | None = None
    ended_at: datetime | None = None
    wait_seconds: int | None = None
    talk_seconds: int | None = None
    allowed_transitions: list[CallStatus] = []
    queue: CallQueueResponse | None = None
    participants: list[CallParticipantResponse] = []
    recordings: list[CallRecordingResponse] = []
    transcripts: list[CallTranscriptResponse] = []
    links: list[CallIncidentLinkResponse] = []
    history: list[CallHistoryResponse] = []


class CallSummaryResponse(ResponseBase):
    number: str
    call_type: CallType
    source: CallSource
    status: CallStatus
    priority: CallPriority
    caller_number: str | None = None
    dispatcher_name: str | None = None
    incident_id: UUID | None = None
    received_at: datetime


class ProviderHealthResponse(SchemaBase):
    healthy: bool
    provider: str
    detail: str | None = None
