"""Shared PostgreSQL enum type objects for the calls module.

Follows the project convention: one ``ENUM`` per type name, ``values_callable``
(lowercase value-labels) and ``create_type=False`` — the new types are created and
dropped exactly once by the calls migration.
"""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy.dialects.postgresql import ENUM

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


def _values(enum_cls: Iterable) -> list[str]:
    return [member.value for member in enum_cls]


def _enum(py_enum, name: str) -> ENUM:
    return ENUM(py_enum, name=name, create_type=False, values_callable=_values)


call_status_enum = _enum(CallStatus, "call_status")
call_priority_enum = _enum(CallPriority, "call_priority")
call_type_enum = _enum(CallType, "call_type")
call_source_enum = _enum(CallSource, "call_source")
call_direction_enum = _enum(CallDirection, "call_direction")
call_event_enum = _enum(CallEventType, "call_event_type")
call_queue_status_enum = _enum(CallQueueStatus, "call_queue_status")
call_participant_role_enum = _enum(CallParticipantRole, "call_participant_role")
call_recording_status_enum = _enum(CallRecordingStatus, "call_recording_status")
call_transcript_status_enum = _enum(CallTranscriptStatus, "call_transcript_status")
call_link_type_enum = _enum(CallLinkType, "call_link_type")

# All new enum types managed explicitly by the calls migration.
NEW_ENUMS = (
    call_status_enum,
    call_priority_enum,
    call_type_enum,
    call_source_enum,
    call_direction_enum,
    call_event_enum,
    call_queue_status_enum,
    call_participant_role_enum,
    call_recording_status_enum,
    call_transcript_status_enum,
    call_link_type_enum,
)

__all__ = [
    "NEW_ENUMS",
    "call_direction_enum",
    "call_event_enum",
    "call_link_type_enum",
    "call_participant_role_enum",
    "call_priority_enum",
    "call_queue_status_enum",
    "call_recording_status_enum",
    "call_source_enum",
    "call_status_enum",
    "call_transcript_status_enum",
    "call_type_enum",
]
