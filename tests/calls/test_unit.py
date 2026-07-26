"""Unit tests for the call lifecycle state machine and the MockCallProvider."""

from __future__ import annotations

import pytest

from app.calls.models.enums import CallDirection, CallSource, CallStatus
from app.calls.providers import MockCallProvider, ProviderCallState
from app.calls.validators.state_machine import (
    ACTIVE_STATUSES,
    CLOSED_STATUSES,
    InvalidCallTransitionError,
    allowed_targets,
    can_transition,
)


def test_happy_path_transitions() -> None:
    path = [
        CallStatus.NEW,
        CallStatus.RINGING,
        CallStatus.ACCEPTED,
        CallStatus.IN_PROGRESS,
        CallStatus.LINKED,
        CallStatus.COMPLETED,
    ]
    for current, target in zip(path, path[1:], strict=False):
        assert can_transition(current, target), f"{current} → {target}"


def test_invalid_transitions_rejected() -> None:
    assert not can_transition(CallStatus.NEW, CallStatus.COMPLETED)
    assert not can_transition(CallStatus.COMPLETED, CallStatus.IN_PROGRESS)
    assert not can_transition(CallStatus.CANCELLED, CallStatus.NEW)


def test_linked_is_reversible_to_in_progress() -> None:
    assert can_transition(CallStatus.LINKED, CallStatus.IN_PROGRESS)
    assert can_transition(CallStatus.LINKED, CallStatus.COMPLETED)


def test_error_is_recoverable() -> None:
    assert can_transition(CallStatus.IN_PROGRESS, CallStatus.ERROR)
    assert can_transition(CallStatus.ERROR, CallStatus.IN_PROGRESS)
    assert can_transition(CallStatus.ERROR, CallStatus.COMPLETED)


def test_terminal_states_have_no_targets() -> None:
    assert allowed_targets(CallStatus.COMPLETED) == frozenset()
    assert allowed_targets(CallStatus.CANCELLED) == frozenset()


def test_active_closed_partition() -> None:
    assert CLOSED_STATUSES == frozenset(
        {CallStatus.COMPLETED, CallStatus.CANCELLED}
    )
    assert CallStatus.NEW in ACTIVE_STATUSES
    assert CallStatus.COMPLETED not in ACTIVE_STATUSES


def test_invalid_transition_error_message() -> None:
    err = InvalidCallTransitionError(CallStatus.NEW, CallStatus.COMPLETED)
    assert "new" in str(err)
    assert "completed" in str(err)


@pytest.mark.asyncio
async def test_mock_provider_full_flow() -> None:
    provider = MockCallProvider()
    health = await provider.health_check()
    assert health.healthy is True
    assert health.provider == "mock"

    handle = await provider.receive_call(
        caller_number="+70000000000", direction=CallDirection.INBOUND,
        source=CallSource.PHONE,
    )
    assert handle.external_id
    assert handle.state is ProviderCallState.RINGING

    answered = await provider.answer_call(handle.external_id)
    assert answered.state is ProviderCallState.ANSWERED
    assert answered.answered_at is not None

    held = await provider.hold_call(handle.external_id)
    assert held.state is ProviderCallState.HELD

    transferred = await provider.transfer_call(
        handle.external_id, destination="102"
    )
    assert transferred.state is ProviderCallState.TRANSFERRED
    assert transferred.meta["transferred_to"] == "102"

    ended = await provider.end_call(handle.external_id)
    assert ended.state is ProviderCallState.ENDED
    assert ended.ended_at is not None


@pytest.mark.asyncio
async def test_mock_provider_unknown_call_raises() -> None:
    from app.core.exceptions import NotFoundError

    provider = MockCallProvider()
    with pytest.raises(NotFoundError):
        await provider.answer_call("does-not-exist")
