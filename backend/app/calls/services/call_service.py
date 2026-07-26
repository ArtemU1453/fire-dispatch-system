"""CallService — the heart of call management.

Registers incoming calls, drives the lifecycle **state machine**, manages the
dispatch **queue**, assigns dispatchers, creates or links **incident** cards
(via the dedicated :class:`CallIncidentLinker`), records an append-only
**history**, and mediates telephony through the pluggable ``CallProvider``.

Only existing services and models are reused; the Dispatch Engine and Incident
Management modules are **not modified**.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.calls.history import CallHistoryRecorder
from app.calls.models.entities import (
    Call,
    CallHistory,
    CallQueueEntry,
    CallRecording,
    CallTranscript,
)
from app.calls.models.enums import (
    CallEventType,
    CallStatus,
)
from app.calls.providers import CallProvider, MockCallProvider, ProviderHealth
from app.calls.queue import CallQueueManager
from app.calls.repositories import CallRepository
from app.calls.services.incident_linker import CallIncidentLinker
from app.calls.utils.actor import Actor
from app.calls.validators.state_machine import (
    InvalidCallTransitionError,
    can_transition,
)
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.incidents.models.enums import IncidentCategory, IncidentPriority

# Statuses at which the call is considered answered / being handled.
_ANSWERED_STATUSES = frozenset(
    {CallStatus.ACCEPTED, CallStatus.IN_PROGRESS, CallStatus.LINKED}
)
_CLOSED_STATUSES = frozenset({CallStatus.COMPLETED, CallStatus.CANCELLED})


def _now() -> datetime:
    return datetime.now(tz=UTC)


class CallService:
    """Application service for the call lifecycle."""

    def __init__(
        self, session: AsyncSession, *, provider: CallProvider | None = None
    ) -> None:
        self._session = session
        self._repo = CallRepository(session)
        self._history = CallHistoryRecorder()
        self._queue = CallQueueManager()
        self._linker = CallIncidentLinker(session)
        self._provider = provider or MockCallProvider()

    # ------------------------------------------------------------- reads
    async def get_call(self, call_id: UUID) -> Call:
        call = await self._repo.get_full(call_id)
        if call is None:
            raise NotFoundError("Call not found")
        return call

    async def list_calls(
        self,
        *,
        active: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Call]:
        return await self._repo.list_calls(
            active=active, limit=limit, offset=offset
        )

    async def get_queue(
        self, *, limit: int = 100, offset: int = 0
    ) -> Sequence[CallQueueEntry]:
        return await self._repo.queue(limit=limit, offset=offset)

    async def get_history(
        self,
        *,
        call_id: UUID | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> Sequence[CallHistory]:
        if call_id is not None:
            await self.get_call(call_id)  # 404 if missing
        return await self._repo.history(
            call_id=call_id, limit=limit, offset=offset
        )

    async def provider_health(self) -> ProviderHealth:
        return await self._provider.health_check()

    # ------------------------------------------------------------- create
    async def create_call(
        self,
        *,
        direction=None,
        call_type=None,
        source=None,
        priority=None,
        caller_number: str | None = None,
        caller_name: str | None = None,
        callee_number: str | None = None,
        address_hint: str | None = None,
        notes: str | None = None,
        external_id: str | None = None,
        register_with_provider: bool = False,
        actor: Actor | None = None,
    ) -> Call:
        """Register a new call and place it in the queue."""
        from app.calls.models.enums import (
            CallDirection,
            CallPriority,
            CallSource,
            CallType,
        )

        actor = actor or Actor()
        number = await self._repo.next_number()
        call = Call(
            number=number,
            external_id=external_id,
            direction=direction or CallDirection.INBOUND,
            call_type=call_type or CallType.EMERGENCY,
            source=source or CallSource.PHONE,
            status=CallStatus.NEW,
            priority=priority or CallPriority.NORMAL,
            caller_number=caller_number,
            caller_name=caller_name,
            callee_number=callee_number,
            address_hint=address_hint,
            notes=notes,
            received_at=_now(),
        )

        # Optionally register with the telephony provider (mock for now).
        if register_with_provider:
            handle = await self._provider.receive_call(
                caller_number=caller_number,
                callee_number=callee_number,
                direction=call.direction,
                source=call.source,
            )
            call.external_id = handle.external_id
            call.status = CallStatus.RINGING

        self._history.record(
            call, CallEventType.CREATED, to_status=call.status,
            actor_name=actor.name, actor_user_id=actor.user_id,
            source=actor.source, detail=number,
        )
        # A new call enters the queue immediately.
        self._queue.enqueue(call)
        self._history.record(
            call, CallEventType.QUEUED, actor_name=actor.name,
            source=actor.source,
        )

        self._session.add(call)
        await self._session.flush()
        return await self.get_call(call.id)

    # ------------------------------------------------------- status change
    async def change_status(
        self,
        call_id: UUID,
        target: CallStatus,
        *,
        note: str | None = None,
        actor: Actor | None = None,
    ) -> Call:
        call = await self.get_call(call_id)
        actor = actor or Actor()
        current = call.status
        if current == target:
            raise ConflictError(f"Call already in status {target.value}")
        if not can_transition(current, target):
            raise ValidationError(str(InvalidCallTransitionError(current, target)))

        call.status = target
        self._apply_status_timestamps(call, target)
        self._sync_queue_for_status(call, target)
        event = self._event_for_status(target)
        self._history.record(
            call, event, from_status=current, to_status=target,
            actor_name=actor.name, actor_user_id=actor.user_id,
            source=actor.source, detail=note,
        )
        await self._session.flush()
        return await self.get_call(call_id)

    async def complete_call(
        self, call_id: UUID, *, actor: Actor | None = None
    ) -> Call:
        return await self.change_status(
            call_id, CallStatus.COMPLETED, actor=actor
        )

    async def cancel_call(
        self, call_id: UUID, *, actor: Actor | None = None
    ) -> Call:
        return await self.change_status(
            call_id, CallStatus.CANCELLED, actor=actor
        )

    # --------------------------------------------------- dispatcher / queue
    async def assign_dispatcher(
        self,
        call_id: UUID,
        *,
        dispatcher_user_id: UUID | None = None,
        dispatcher_name: str | None = None,
        workstation: str | None = None,
        actor: Actor | None = None,
    ) -> Call:
        call = await self.get_call(call_id)
        actor = actor or Actor()
        call.dispatcher_user_id = dispatcher_user_id
        call.dispatcher_name = dispatcher_name
        entry = call.queue_entry
        if entry is None or entry.is_deleted:
            entry = self._queue.enqueue(call)
        self._queue.assign(
            entry, dispatcher_user_id=dispatcher_user_id,
            dispatcher_name=dispatcher_name, workstation=workstation,
        )
        # Convenience: a new/ringing call becomes "accepted" once picked up.
        if can_transition(call.status, CallStatus.ACCEPTED):
            call.status = CallStatus.ACCEPTED
            self._apply_status_timestamps(call, CallStatus.ACCEPTED)
        self._history.record(
            call, CallEventType.DISPATCHER_ASSIGNED,
            to_status=call.status, actor_name=actor.name,
            actor_user_id=actor.user_id, source=actor.source,
            detail=dispatcher_name or (workstation or None),
        )
        await self._session.flush()
        return await self.get_call(call_id)

    # -------------------------------------------------- incident (link/create)
    async def attach_incident(
        self,
        call_id: UUID,
        *,
        incident_id: UUID | None = None,
        create: bool = False,
        incident_type_id: UUID | None = None,
        category: IncidentCategory = IncidentCategory.OTHER,
        priority: IncidentPriority = IncidentPriority.NORMAL,
        title: str | None = None,
        description: str | None = None,
        address: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        actor: Actor | None = None,
    ) -> Call:
        call = await self.get_call(call_id)
        actor = actor or Actor()
        self._linker.require_choice(incident_id, create=create)

        if create:
            incident = await self._linker.create_incident_for_call(
                call, incident_type_id=incident_type_id, category=category,
                priority=priority, title=title, description=description,
                address=address, latitude=latitude, longitude=longitude,
                actor=actor,
            )
            event = CallEventType.INCIDENT_CREATED
        else:
            incident = await self._linker.link_existing(
                call, incident_id, actor=actor
            )
            event = CallEventType.INCIDENT_LINKED

        # Move the call to "linked" when the lifecycle allows it.
        if can_transition(call.status, CallStatus.LINKED):
            call.status = CallStatus.LINKED
            self._apply_status_timestamps(call, CallStatus.LINKED)
        self._history.record(
            call, event, to_status=call.status, incident_id=incident.id,
            actor_name=actor.name, actor_user_id=actor.user_id,
            source=actor.source, meta={"incident_id": str(incident.id)},
        )
        await self._session.flush()
        return await self.get_call(call_id)

    # ----------------------------------------------------- telephony actions
    async def answer_call(
        self, call_id: UUID, *, actor: Actor | None = None
    ) -> Call:
        call = await self.get_call(call_id)
        actor = actor or Actor()
        if call.external_id:
            await self._provider.answer_call(call.external_id)
        if can_transition(call.status, CallStatus.ACCEPTED):
            call.status = CallStatus.ACCEPTED
            self._apply_status_timestamps(call, CallStatus.ACCEPTED)
        self._history.record(
            call, CallEventType.ANSWERED, to_status=call.status,
            actor_name=actor.name, source=actor.source,
        )
        await self._session.flush()
        return await self.get_call(call_id)

    async def hold_call(
        self, call_id: UUID, *, actor: Actor | None = None
    ) -> Call:
        return await self._provider_action(
            call_id, "hold", actor=actor
        )

    async def transfer_call(
        self, call_id: UUID, *, destination: str, actor: Actor | None = None
    ) -> Call:
        return await self._provider_action(
            call_id, "transfer", destination=destination, actor=actor
        )

    async def end_call(
        self, call_id: UUID, *, actor: Actor | None = None
    ) -> Call:
        """End the telephony leg and complete the call."""
        call = await self.get_call(call_id)
        actor = actor or Actor()
        if call.external_id:
            await self._provider.end_call(call.external_id)
        if can_transition(call.status, CallStatus.COMPLETED):
            return await self.change_status(
                call_id, CallStatus.COMPLETED, actor=actor
            )
        self._history.record(
            call, CallEventType.PROVIDER_ACTION, actor_name=actor.name,
            source=actor.source, detail="end",
        )
        await self._session.flush()
        return await self.get_call(call_id)

    # ---------------------------------------- recordings / transcripts (seams)
    async def register_recording(
        self,
        call_id: UUID,
        *,
        external_ref: str | None = None,
        audio_format: str | None = None,
        duration_seconds: int | None = None,
        storage_ref: str | None = None,
        actor: Actor | None = None,
    ) -> CallRecording:
        """Register recording **metadata** (no audio is captured at this stage)."""
        call = await self.get_call(call_id)
        actor = actor or Actor()
        recording = CallRecording(
            external_ref=external_ref, audio_format=audio_format,
            duration_seconds=duration_seconds, storage_ref=storage_ref,
        )
        call.recordings.append(recording)
        self._history.record(
            call, CallEventType.RECORDING_REGISTERED, actor_name=actor.name,
            source=actor.source,
        )
        await self._session.flush()
        return recording

    async def register_transcript(
        self,
        call_id: UUID,
        *,
        language: str | None = "ru",
        text_content: str | None = None,
        segments: dict | None = None,
        engine: str | None = None,
        actor: Actor | None = None,
    ) -> CallTranscript:
        """Register a transcript **placeholder** (no ASR at this stage)."""
        call = await self.get_call(call_id)
        actor = actor or Actor()
        transcript = CallTranscript(
            language=language, text_content=text_content, segments=segments,
            engine=engine,
        )
        call.transcripts.append(transcript)
        self._history.record(
            call, CallEventType.TRANSCRIPT_REGISTERED, actor_name=actor.name,
            source=actor.source,
        )
        await self._session.flush()
        return transcript

    # ------------------------------------------------------------ helpers
    async def _provider_action(
        self,
        call_id: UUID,
        action: str,
        *,
        destination: str | None = None,
        actor: Actor | None = None,
    ) -> Call:
        call = await self.get_call(call_id)
        actor = actor or Actor()
        if call.external_id:
            if action == "hold":
                await self._provider.hold_call(call.external_id)
            elif action == "transfer":
                await self._provider.transfer_call(
                    call.external_id, destination=destination or ""
                )
        self._history.record(
            call, CallEventType.PROVIDER_ACTION, actor_name=actor.name,
            source=actor.source, detail=action,
            meta={"destination": destination} if destination else None,
        )
        await self._session.flush()
        return await self.get_call(call_id)

    def _apply_status_timestamps(self, call: Call, target: CallStatus) -> None:
        now = _now()
        if target in _ANSWERED_STATUSES and call.answered_at is None:
            call.answered_at = now
            call.wait_seconds = max(
                0, int((now - call.received_at).total_seconds())
            )
        if target in _CLOSED_STATUSES:
            call.ended_at = now
            if call.answered_at is not None:
                call.talk_seconds = max(
                    0, int((now - call.answered_at).total_seconds())
                )

    def _sync_queue_for_status(self, call: Call, target: CallStatus) -> None:
        entry = call.queue_entry
        if entry is None or entry.is_deleted:
            return
        if target == CallStatus.IN_PROGRESS:
            self._queue.mark_in_progress(entry)
        elif target in _CLOSED_STATUSES:
            abandoned = (
                target == CallStatus.CANCELLED and call.answered_at is None
            )
            self._queue.remove(entry, abandoned=abandoned)

    @staticmethod
    def _event_for_status(target: CallStatus) -> CallEventType:
        return {
            CallStatus.COMPLETED: CallEventType.COMPLETED,
            CallStatus.CANCELLED: CallEventType.CANCELLED,
            CallStatus.ERROR: CallEventType.ERROR,
            CallStatus.LINKED: CallEventType.INCIDENT_LINKED,
        }.get(target, CallEventType.STATUS_CHANGED)
