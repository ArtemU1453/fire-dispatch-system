"""Responder status state machine (Stage 19).

The unit lifecycle a responder reports from the field. Transitions are validated
**on the server** (the app only sends the requested status; the server decides
whether it is allowed), satisfying "no business logic in the app".
"""

from __future__ import annotations

import enum


class ResponderStatus(str, enum.Enum):
    ASSIGNED = "assigned"        # получено задание
    EN_ROUTE = "en_route"        # выезд
    ON_SCENE = "on_scene"        # прибыл
    WORKING = "working"          # работает
    RETURNING = "returning"      # возвращается
    COMPLETED = "completed"      # завершил


# Allowed forward transitions. A unit may also be re-assigned from terminal.
_TRANSITIONS: dict[ResponderStatus, set[ResponderStatus]] = {
    ResponderStatus.ASSIGNED: {ResponderStatus.EN_ROUTE},
    ResponderStatus.EN_ROUTE: {ResponderStatus.ON_SCENE, ResponderStatus.RETURNING},
    ResponderStatus.ON_SCENE: {ResponderStatus.WORKING, ResponderStatus.RETURNING},
    ResponderStatus.WORKING: {ResponderStatus.RETURNING, ResponderStatus.COMPLETED},
    ResponderStatus.RETURNING: {ResponderStatus.COMPLETED},
    ResponderStatus.COMPLETED: set(),
}


class InvalidStatusTransition(ValueError):
    pass


def can_transition(current: ResponderStatus, target: ResponderStatus) -> bool:
    return target in _TRANSITIONS.get(current, set())


def validate_transition(current: ResponderStatus, target: ResponderStatus) -> None:
    if not can_transition(current, target):
        raise InvalidStatusTransition(
            f"cannot go from {current.value} to {target.value}"
        )


class ResponderStateStore:
    """Tracks each unit's current responder status (in-memory BFF state)."""

    def __init__(self) -> None:
        self._state: dict[str, ResponderStatus] = {}

    def current(self, unit_id: str) -> ResponderStatus:
        return self._state.get(unit_id, ResponderStatus.ASSIGNED)

    def set(self, unit_id: str, status: ResponderStatus) -> ResponderStatus:
        self._state[unit_id] = status
        return status

    def transition(
        self, unit_id: str, target: ResponderStatus
    ) -> ResponderStatus:
        current = self.current(unit_id)
        validate_transition(current, target)
        return self.set(unit_id, target)
