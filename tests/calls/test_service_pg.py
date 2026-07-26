"""Integration tests for CallService (require PostgreSQL)."""

from __future__ import annotations

from uuid import UUID

import pytest

from app.calls.models.enums import (
    CallEventType,
    CallLinkType,
    CallPriority,
    CallQueueStatus,
    CallStatus,
)
from app.calls.providers import MockCallProvider
from app.calls.services import CallService
from app.core.exceptions import ConflictError, ValidationError
from app.incidents.models.enums import IncidentCategory

from .conftest import CallSeed

pytestmark = pytest.mark.asyncio


async def test_create_call_enters_queue_and_history(pg_factory) -> None:
    async with pg_factory() as s:
        service = CallService(s)
        call = await service.create_call(
            caller_number="+70001112233", caller_name="Иванов",
            notes="Задымление", actor=None,
        )
        await s.commit()
        call_id = call.id

    async with pg_factory() as s:
        call = await CallService(s).get_call(call_id)
        assert call.status is CallStatus.NEW
        assert call.number.startswith("CALL-")
        assert call.queue_entry is not None
        assert call.queue_entry.status is CallQueueStatus.WAITING
        events = {h.event_type for h in call.history}
        assert CallEventType.CREATED in events
        assert CallEventType.QUEUED in events


async def test_status_progression_and_timestamps(pg_factory) -> None:
    async with pg_factory() as s:
        service = CallService(s)
        call = await service.create_call()
        await s.commit()
        cid = call.id

    async with pg_factory() as s:
        service = CallService(s)
        call = await service.change_status(cid, CallStatus.ACCEPTED)
        assert call.answered_at is not None
        assert call.wait_seconds is not None
        call = await service.change_status(cid, CallStatus.IN_PROGRESS)
        assert call.queue_entry.status is CallQueueStatus.IN_PROGRESS
        call = await service.change_status(cid, CallStatus.COMPLETED)
        assert call.ended_at is not None
        assert call.queue_entry.status is CallQueueStatus.DONE
        await s.commit()


async def test_invalid_transition_rejected(pg_factory) -> None:
    async with pg_factory() as s:
        service = CallService(s)
        call = await service.create_call()
        await s.commit()
        cid = call.id

    async with pg_factory() as s:
        service = CallService(s)
        with pytest.raises(ValidationError):
            await service.change_status(cid, CallStatus.COMPLETED)


async def test_same_status_conflicts(pg_factory) -> None:
    async with pg_factory() as s:
        service = CallService(s)
        call = await service.create_call()
        await s.commit()
        cid = call.id

    async with pg_factory() as s:
        service = CallService(s)
        with pytest.raises(ConflictError):
            await service.change_status(cid, CallStatus.NEW)


async def test_assign_dispatcher_accepts_and_assigns_queue(pg_factory) -> None:
    async with pg_factory() as s:
        service = CallService(s)
        call = await service.create_call()
        await s.commit()
        cid = call.id

    async with pg_factory() as s:
        service = CallService(s)
        call = await service.assign_dispatcher(
            cid, dispatcher_name="Диспетчер-1", workstation="WS-1"
        )
        assert call.dispatcher_name == "Диспетчер-1"
        assert call.status is CallStatus.ACCEPTED
        assert call.queue_entry.status is CallQueueStatus.ASSIGNED
        assert call.queue_entry.workstation == "WS-1"
        await s.commit()


async def test_attach_incident_creates_new(pg_factory, seed: CallSeed) -> None:
    async with pg_factory() as s:
        service = CallService(s)
        call = await service.create_call(notes="Пожар в доме")
        await s.commit()
        cid = call.id

    async with pg_factory() as s:
        service = CallService(s)
        call = await service.attach_incident(
            cid, create=True,
            incident_type_id=UUID(seed.incident_type_id),
            category=IncidentCategory.FIRE,
        )
        assert call.incident_id is not None
        assert call.status is CallStatus.LINKED
        links = [link for link in call.links if not link.is_deleted]
        assert len(links) == 1
        assert links[0].link_type is CallLinkType.CREATED
        assert links[0].is_primary is True
        await s.commit()


async def test_attach_incident_links_existing(pg_factory, seed: CallSeed) -> None:
    async with pg_factory() as s:
        service = CallService(s)
        call = await service.create_call()
        await s.commit()
        cid = call.id

    async with pg_factory() as s:
        service = CallService(s)
        call = await service.attach_incident(
            cid, incident_id=UUID(seed.incident_id)
        )
        assert str(call.incident_id) == seed.incident_id
        links = [link for link in call.links if not link.is_deleted]
        assert links[0].link_type is CallLinkType.LINKED
        # history records the incident link with the incident id
        linked = [
            h for h in call.history
            if h.event_type is CallEventType.INCIDENT_LINKED
        ]
        assert linked and str(linked[0].incident_id) == seed.incident_id
        await s.commit()


async def test_attach_incident_requires_exactly_one_choice(
    pg_factory, seed: CallSeed
) -> None:
    async with pg_factory() as s:
        service = CallService(s)
        call = await service.create_call()
        await s.commit()
        cid = call.id

    async with pg_factory() as s:
        service = CallService(s)
        with pytest.raises(ValidationError):  # neither
            await service.attach_incident(cid)
        with pytest.raises(ValidationError):  # both
            await service.attach_incident(
                cid, incident_id=UUID(seed.incident_id), create=True
            )


async def test_queue_ordered_by_priority(pg_factory) -> None:
    async with pg_factory() as s:
        service = CallService(s)
        await service.create_call(priority=CallPriority.LOW, notes="low")
        await service.create_call(priority=CallPriority.CRITICAL, notes="crit")
        await service.create_call(priority=CallPriority.NORMAL, notes="norm")
        await s.commit()

    async with pg_factory() as s:
        service = CallService(s)
        entries = await service.get_queue()
        priorities = [e.priority for e in entries]
        # Critical must come before normal, normal before low.
        assert priorities.index(CallPriority.CRITICAL) < priorities.index(
            CallPriority.NORMAL
        )
        assert priorities.index(CallPriority.NORMAL) < priorities.index(
            CallPriority.LOW
        )


async def test_provider_flow_answer_and_end(pg_factory) -> None:
    provider = MockCallProvider()
    async with pg_factory() as s:
        service = CallService(s, provider=provider)
        call = await service.create_call(register_with_provider=True)
        assert call.external_id is not None
        assert call.status is CallStatus.RINGING
        await s.commit()
        cid = call.id

    async with pg_factory() as s:
        service = CallService(s, provider=provider)
        call = await service.answer_call(cid)
        assert call.status is CallStatus.ACCEPTED
        call = await service.end_call(cid)
        assert call.status is CallStatus.COMPLETED
        await s.commit()


async def test_register_recording_and_transcript(pg_factory) -> None:
    async with pg_factory() as s:
        service = CallService(s)
        call = await service.create_call()
        await service.register_recording(
            call.id, external_ref="rec-1", audio_format="wav",
            duration_seconds=42,
        )
        await service.register_transcript(
            call.id, text_content="Пожар по адресу ...", language="ru",
        )
        await s.commit()
        cid = call.id

    async with pg_factory() as s:
        call = await CallService(s).get_call(cid)
        assert len(call.recordings) == 1
        assert call.recordings[0].external_ref == "rec-1"
        assert len(call.transcripts) == 1
        assert call.transcripts[0].language == "ru"


async def test_history_is_append_only(pg_factory) -> None:
    async with pg_factory() as s:
        service = CallService(s)
        call = await service.create_call()
        await service.change_status(call.id, CallStatus.ACCEPTED)
        await service.change_status(call.id, CallStatus.IN_PROGRESS)
        await s.commit()
        cid = call.id

    async with pg_factory() as s:
        rows = await CallService(s).get_history(call_id=cid)
        to_values = [h.to_status for h in rows if h.to_status]
        assert CallStatus.ACCEPTED in to_values
        assert CallStatus.IN_PROGRESS in to_values
        # append-only: creation + queue + 2 status changes ≥ 4 entries
        assert len(rows) >= 4
