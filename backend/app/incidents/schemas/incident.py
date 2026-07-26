"""Pydantic schemas for incident management."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

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
from app.schemas.common import ResponseBase, SchemaBase


# ------------------------------------------------------------------ nested ---
class LocationResponse(ResponseBase):
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    administrative_area_id: UUID | None = None
    accuracy: str | None = None
    source: str | None = None
    is_primary: bool


class ParticipantResponse(ResponseBase):
    role: str
    name: str | None = None
    contact: str | None = None
    organization_id: UUID | None = None
    note: str | None = None


class CommentResponse(ResponseBase):
    author_user_id: UUID | None = None
    author_name: str | None = None
    text: str


class AttachmentResponse(ResponseBase):
    kind: AttachmentKind
    filename: str
    content_type: str | None = None
    size_bytes: int | None = None
    storage_ref: str | None = None
    description: str | None = None


class TimelineEntryResponse(ResponseBase):
    event_type: TimelineEventType
    title: str
    detail: str | None = None
    actor_name: str | None = None
    meta: dict[str, Any] | None = None
    occurred_at: datetime


class HistoryEntryResponse(ResponseBase):
    field: str
    old_value: str | None = None
    new_value: str | None = None
    change_source: ChangeSource
    changed_by_name: str | None = None
    note: str | None = None
    occurred_at: datetime


class RecommendationLinkResponse(ResponseBase):
    recommendation_id: UUID | None = None
    is_current: bool
    note: str | None = None


class DispatchUnitResponse(ResponseBase):
    resource_id: UUID
    role: str
    status: DispatchUnitStatus
    assigned_at: datetime
    note: str | None = None


class LogResponse(ResponseBase):
    action: str
    message: str | None = None
    level: str
    occurred_at: datetime


# ------------------------------------------------------------------ inputs ---
class IncidentCreate(SchemaBase):
    number: str | None = None  # auto-generated when omitted
    incident_type_id: UUID | None = None
    category: IncidentCategory = IncidentCategory.OTHER
    source: IncidentSource = IncidentSource.PHONE
    priority: IncidentPriority = IncidentPriority.NORMAL
    title: str | None = None
    description: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    administrative_area_id: UUID | None = None
    danger_level: str | None = None
    object_type: str | None = None
    reporter_name: str | None = None
    reporter_contact: str | None = None
    actor_name: str | None = None


class IncidentUpdate(SchemaBase):
    incident_type_id: UUID | None = None
    category: IncidentCategory | None = None
    source: IncidentSource | None = None
    priority: IncidentPriority | None = None
    title: str | None = None
    description: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    administrative_area_id: UUID | None = None
    danger_level: str | None = None
    object_type: str | None = None
    reporter_name: str | None = None
    reporter_contact: str | None = None
    actor_name: str | None = None


class StatusChangeRequest(SchemaBase):
    status: IncidentStatus
    note: str | None = None
    actor_name: str | None = None


class CommentCreate(SchemaBase):
    text: str
    author_name: str | None = None


class AssignUnitInput(SchemaBase):
    resource_id: UUID
    role: str = "primary"
    note: str | None = None


class AssignUnitsRequest(SchemaBase):
    units: list[AssignUnitInput]
    recommendation_id: UUID | None = None
    actor_name: str | None = None


# --------------------------------------------------------------- responses ---
class IncidentResponse(ResponseBase):
    number: str
    incident_type_id: UUID | None = None
    category: IncidentCategory
    source: IncidentSource
    status: IncidentStatus
    priority: IncidentPriority
    title: str | None = None
    description: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    administrative_area_id: UUID | None = None
    danger_level: str | None = None
    object_type: str | None = None
    reporter_name: str | None = None
    reporter_contact: str | None = None
    reported_at: datetime
    confirmed_at: datetime | None = None
    closed_at: datetime | None = None
    archived_at: datetime | None = None
    allowed_transitions: list[IncidentStatus] = []
    locations: list[LocationResponse] = []
    participants: list[ParticipantResponse] = []
    comments: list[CommentResponse] = []
    attachments: list[AttachmentResponse] = []
    timeline: list[TimelineEntryResponse] = []
    history: list[HistoryEntryResponse] = []
    recommendations: list[RecommendationLinkResponse] = []
    dispatches: list[DispatchUnitResponse] = []


class IncidentSummaryResponse(ResponseBase):
    number: str
    category: IncidentCategory
    status: IncidentStatus
    priority: IncidentPriority
    title: str | None = None
    address: str | None = None
    reported_at: datetime


class StatusResponse(SchemaBase):
    id: UUID
    status: IncidentStatus
    allowed_transitions: list[IncidentStatus]
    changed_at: datetime


class IncidentTimelineResponse(SchemaBase):
    incident_id: UUID
    count: int
    entries: list[TimelineEntryResponse]
