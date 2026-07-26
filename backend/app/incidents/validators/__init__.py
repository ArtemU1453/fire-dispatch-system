"""Incident validators (lifecycle state machine)."""

from __future__ import annotations

from app.incidents.validators.state_machine import (
    ACTIVE_STATUSES,
    CLOSED_STATUSES,
    TRANSITIONS,
    InvalidTransitionError,
    allowed_targets,
    can_transition,
)

__all__ = [
    "ACTIVE_STATUSES",
    "CLOSED_STATUSES",
    "TRANSITIONS",
    "InvalidTransitionError",
    "allowed_targets",
    "can_transition",
]
