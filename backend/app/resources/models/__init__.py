"""Resource-management ORM models and enums."""

from __future__ import annotations

from app.resources.models.entities import (
    Crew,
    CrewMember,
    DutyRoster,
    PersonnelQualification,
    ResourceAssignment,
    ResourceManagementHistory,
    Shift,
    Unit,
    VehicleState,
)
from app.resources.models.enums import (
    AssignmentStatus,
    QualificationKind,
    ResourceEventType,
    TechnicalCondition,
)

__all__ = [
    "AssignmentStatus",
    "Crew",
    "CrewMember",
    "DutyRoster",
    "PersonnelQualification",
    "QualificationKind",
    "ResourceAssignment",
    "ResourceEventType",
    "ResourceManagementHistory",
    "Shift",
    "TechnicalCondition",
    "Unit",
    "VehicleState",
]
