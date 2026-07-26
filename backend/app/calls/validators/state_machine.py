"""Call lifecycle — a finite state machine.

Encodes the allowed status transitions. The service consults this before any
status change and **rejects invalid transitions**, so a call can only move along
its defined lifecycle:

    new → ringing → accepted → in_progress → linked → completed

A call may be **cancelled** before it is completed, and may enter the **error**
state from any non-terminal status (from which it can be recovered or closed).
Linking to an incident (``linked``) is reversible back to ``in_progress`` so a
call can be attached to several incidents in sequence.
"""

from __future__ import annotations

from app.calls.models.enums import CallStatus

_S = CallStatus

# Allowed transitions: status → set of statuses it may move to.
TRANSITIONS: dict[CallStatus, frozenset[CallStatus]] = {
    _S.NEW: frozenset(
        {_S.RINGING, _S.ACCEPTED, _S.LINKED, _S.CANCELLED, _S.ERROR}
    ),
    _S.RINGING: frozenset(
        {_S.ACCEPTED, _S.LINKED, _S.CANCELLED, _S.ERROR}
    ),
    _S.ACCEPTED: frozenset(
        {_S.IN_PROGRESS, _S.LINKED, _S.COMPLETED, _S.CANCELLED, _S.ERROR}
    ),
    _S.IN_PROGRESS: frozenset(
        {_S.LINKED, _S.COMPLETED, _S.CANCELLED, _S.ERROR}
    ),
    _S.LINKED: frozenset(
        {_S.IN_PROGRESS, _S.COMPLETED, _S.CANCELLED, _S.ERROR}
    ),
    _S.COMPLETED: frozenset(),
    _S.CANCELLED: frozenset(),
    _S.ERROR: frozenset({_S.IN_PROGRESS, _S.COMPLETED, _S.CANCELLED}),
}

# Statuses that mark the call as closed (no active handling).
CLOSED_STATUSES: frozenset[CallStatus] = frozenset(
    {_S.COMPLETED, _S.CANCELLED}
)
ACTIVE_STATUSES: frozenset[CallStatus] = frozenset(
    s for s in CallStatus if s not in CLOSED_STATUSES
)


def can_transition(current: CallStatus, target: CallStatus) -> bool:
    """True if moving from ``current`` to ``target`` is allowed."""
    return target in TRANSITIONS.get(current, frozenset())


def allowed_targets(current: CallStatus) -> frozenset[CallStatus]:
    return TRANSITIONS.get(current, frozenset())


class InvalidCallTransitionError(Exception):
    """Raised when a status change is not permitted by the state machine."""

    def __init__(self, current: CallStatus, target: CallStatus) -> None:
        self.current = current
        self.target = target
        super().__init__(
            f"Недопустимый переход статуса вызова: {current.value} → {target.value}"
        )
