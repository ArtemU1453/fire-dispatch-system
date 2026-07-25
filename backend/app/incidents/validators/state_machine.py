"""Incident lifecycle — a finite state machine.

Encodes the allowed status transitions. The service consults this before any
status change and **rejects invalid transitions**, so an incident can only move
along its defined lifecycle:

    created → checking → confirmed → selecting → dispatch_confirmed →
    dispatched → on_scene → localized → liquidated → completed → archived

An incident may be **cancelled** from any pre-dispatch state; cancelled and
completed incidents may be archived. Terminal states have no outgoing
transitions.
"""

from __future__ import annotations

from app.incidents.models.enums import IncidentStatus

_S = IncidentStatus

# Allowed transitions: status → set of statuses it may move to.
TRANSITIONS: dict[IncidentStatus, frozenset[IncidentStatus]] = {
    _S.CREATED: frozenset({_S.CHECKING, _S.CANCELLED}),
    _S.CHECKING: frozenset({_S.CONFIRMED, _S.CANCELLED}),
    _S.CONFIRMED: frozenset({_S.SELECTING, _S.CANCELLED}),
    _S.SELECTING: frozenset({_S.DISPATCH_CONFIRMED, _S.CANCELLED}),
    _S.DISPATCH_CONFIRMED: frozenset({_S.DISPATCHED, _S.CANCELLED}),
    _S.DISPATCHED: frozenset({_S.ON_SCENE}),
    _S.ON_SCENE: frozenset({_S.LOCALIZED}),
    _S.LOCALIZED: frozenset({_S.LIQUIDATED}),
    _S.LIQUIDATED: frozenset({_S.COMPLETED}),
    _S.COMPLETED: frozenset({_S.ARCHIVED}),
    _S.CANCELLED: frozenset({_S.ARCHIVED}),
    _S.ARCHIVED: frozenset(),
}

# Statuses that mark the incident as closed (no active work).
CLOSED_STATUSES: frozenset[IncidentStatus] = frozenset(
    {_S.COMPLETED, _S.CANCELLED, _S.ARCHIVED}
)
ACTIVE_STATUSES: frozenset[IncidentStatus] = frozenset(
    s for s in IncidentStatus if s not in CLOSED_STATUSES
)


def can_transition(current: IncidentStatus, target: IncidentStatus) -> bool:
    """True if moving from ``current`` to ``target`` is allowed."""
    return target in TRANSITIONS.get(current, frozenset())


def allowed_targets(current: IncidentStatus) -> frozenset[IncidentStatus]:
    return TRANSITIONS.get(current, frozenset())


class InvalidTransitionError(Exception):
    """Raised when a status change is not permitted by the state machine."""

    def __init__(self, current: IncidentStatus, target: IncidentStatus) -> None:
        self.current = current
        self.target = target
        super().__init__(
            f"Недопустимый переход статуса: {current.value} → {target.value}"
        )
