"""Unit tests for the incident lifecycle state machine (no database)."""

from __future__ import annotations

from app.incidents.models.enums import IncidentStatus as S
from app.incidents.validators.state_machine import (
    ACTIVE_STATUSES,
    CLOSED_STATUSES,
    allowed_targets,
    can_transition,
)


def test_full_lifecycle_path_is_valid() -> None:
    path = [
        S.CREATED, S.CHECKING, S.CONFIRMED, S.SELECTING, S.DISPATCH_CONFIRMED,
        S.DISPATCHED, S.ON_SCENE, S.LOCALIZED, S.LIQUIDATED, S.COMPLETED, S.ARCHIVED,
    ]
    for current, target in zip(path, path[1:], strict=False):
        assert can_transition(current, target), f"{current} → {target}"


def test_invalid_jumps_are_rejected() -> None:
    assert not can_transition(S.CREATED, S.DISPATCHED)
    assert not can_transition(S.CREATED, S.COMPLETED)
    assert not can_transition(S.ON_SCENE, S.CREATED)  # no going back
    assert not can_transition(S.ARCHIVED, S.COMPLETED)  # terminal


def test_cancel_only_before_dispatch() -> None:
    assert can_transition(S.CREATED, S.CANCELLED)
    assert can_transition(S.SELECTING, S.CANCELLED)
    assert not can_transition(S.DISPATCHED, S.CANCELLED)
    assert not can_transition(S.ON_SCENE, S.CANCELLED)


def test_terminal_states_have_no_targets() -> None:
    assert allowed_targets(S.ARCHIVED) == frozenset()


def test_active_and_closed_partition() -> None:
    assert S.CREATED in ACTIVE_STATUSES
    assert S.DISPATCHED in ACTIVE_STATUSES
    assert S.COMPLETED in CLOSED_STATUSES
    assert S.ARCHIVED in CLOSED_STATUSES
    assert S.CANCELLED in CLOSED_STATUSES
    assert ACTIVE_STATUSES.isdisjoint(CLOSED_STATUSES)
