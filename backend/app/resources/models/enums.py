"""Enumerations for real-time resource / unit management.

Statuses of units, vehicles and personnel are **not** enums — they live in the
database (the Stage-2 ``availability_statuses`` catalog) so they can change
without code. These enums cover the module's own structured fields.
"""

from __future__ import annotations

from enum import Enum


class TechnicalCondition(str, Enum):
    """Technical condition of a vehicle."""

    OPERATIONAL = "operational"
    NEEDS_SERVICE = "needs_service"
    UNDER_REPAIR = "under_repair"
    DECOMMISSIONED = "decommissioned"


class QualificationKind(str, Enum):
    """Kind of a personnel qualification record.

    ``medical`` is reserved for future medical restrictions; ``clearance`` for
    special admissions (допуски). The architecture supports them now.
    """

    QUALIFICATION = "qualification"
    CLEARANCE = "clearance"
    MEDICAL = "medical"


class AssignmentStatus(str, Enum):
    """Status of a unit's assignment to an incident."""

    ACTIVE = "active"
    RELEASED = "released"
    CANCELLED = "cancelled"


class ResourceEventType(str, Enum):
    """Kinds of events recorded in the (append-only) management history."""

    UNIT_STATUS_CHANGED = "unit_status_changed"
    VEHICLE_STATUS_CHANGED = "vehicle_status_changed"
    PERSONNEL_STATUS_CHANGED = "personnel_status_changed"
    CREW_CHANGED = "crew_changed"
    CREW_MEMBER_CHANGED = "crew_member_changed"
    ASSIGNED = "assigned"
    RETURNED = "returned"
