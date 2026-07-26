"""Mapping between call-management ORM objects and API schemas."""

from __future__ import annotations

from app.calls.models.entities import Call, CallHistory, CallQueueEntry
from app.calls.queue import wait_seconds
from app.calls.schemas.call import (
    CallHistoryResponse,
    CallIncidentLinkResponse,
    CallParticipantResponse,
    CallQueueResponse,
    CallRecordingResponse,
    CallResponse,
    CallSummaryResponse,
    CallTranscriptResponse,
)
from app.calls.validators.state_machine import allowed_targets


def _queue_to_response(
    entry: CallQueueEntry, *, call: Call | None = None
) -> CallQueueResponse:
    return CallQueueResponse(
        id=entry.id,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        is_deleted=entry.is_deleted,
        call_id=entry.call_id,
        priority=entry.priority,
        status=entry.status,
        enqueued_at=entry.enqueued_at,
        assigned_at=entry.assigned_at,
        removed_at=entry.removed_at,
        dispatcher_user_id=entry.dispatcher_user_id,
        dispatcher_name=entry.dispatcher_name,
        workstation=entry.workstation,
        wait_seconds=wait_seconds(entry),
        call_number=call.number if call else None,
        caller_number=call.caller_number if call else None,
        call_status=call.status if call else None,
    )


def queue_entry_to_response(entry: CallQueueEntry) -> CallQueueResponse:
    """Map a queue entry (with its loaded ``call``) for the dispatcher board."""
    return _queue_to_response(entry, call=entry.call)


def _history_to_response(entry: CallHistory) -> CallHistoryResponse:
    return CallHistoryResponse.model_validate(entry)


def history_to_response(entry: CallHistory) -> CallHistoryResponse:
    return _history_to_response(entry)


def call_to_response(call: Call) -> CallResponse:
    live = [link for link in call.links if not link.is_deleted]
    history = sorted(
        call.history, key=lambda h: h.occurred_at, reverse=True
    )
    queue = (
        _queue_to_response(call.queue_entry)
        if call.queue_entry is not None and not call.queue_entry.is_deleted
        else None
    )
    return CallResponse(
        id=call.id,
        created_at=call.created_at,
        updated_at=call.updated_at,
        is_deleted=call.is_deleted,
        number=call.number,
        external_id=call.external_id,
        direction=call.direction,
        call_type=call.call_type,
        source=call.source,
        status=call.status,
        priority=call.priority,
        caller_number=call.caller_number,
        caller_name=call.caller_name,
        callee_number=call.callee_number,
        address_hint=call.address_hint,
        dispatcher_user_id=call.dispatcher_user_id,
        dispatcher_name=call.dispatcher_name,
        incident_id=call.incident_id,
        notes=call.notes,
        received_at=call.received_at,
        answered_at=call.answered_at,
        ended_at=call.ended_at,
        wait_seconds=call.wait_seconds,
        talk_seconds=call.talk_seconds,
        allowed_transitions=sorted(allowed_targets(call.status), key=lambda s: s.value),
        queue=queue,
        participants=[
            CallParticipantResponse.model_validate(p)
            for p in call.participants
            if not p.is_deleted
        ],
        recordings=[
            CallRecordingResponse.model_validate(r)
            for r in call.recordings
            if not r.is_deleted
        ],
        transcripts=[
            CallTranscriptResponse.model_validate(t)
            for t in call.transcripts
            if not t.is_deleted
        ],
        links=[CallIncidentLinkResponse.model_validate(link) for link in live],
        history=[_history_to_response(h) for h in history],
    )


def call_to_summary(call: Call) -> CallSummaryResponse:
    return CallSummaryResponse.model_validate(call)
