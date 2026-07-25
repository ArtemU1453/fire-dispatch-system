"""Readiness classification helper.

Maps a resource's availability status (a catalog row) to a readiness state used
by scoring — model-driven, so which statuses count as deployable is data, not
code.
"""

from __future__ import annotations

from app.dispatch.algorithms.scoring import (
    READY_DEPLOYABLE,
    READY_OPERATIONAL,
    READY_OTHER,
)
from app.models.resource import Resource


def readiness_of(resource: Resource) -> str:
    status = resource.availability_status
    if status is None:
        return READY_OTHER
    if status.is_available_for_dispatch:
        return READY_DEPLOYABLE
    if status.is_operational:
        return READY_OPERATIONAL
    return READY_OTHER
