"""Shared PostgreSQL enum type objects for the resource-management module."""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy.dialects.postgresql import ENUM

from app.resources.models.enums import (
    AssignmentStatus,
    QualificationKind,
    ResourceEventType,
    TechnicalCondition,
)


def _values(enum_cls: Iterable) -> list[str]:
    return [member.value for member in enum_cls]


def _enum(py_enum, name: str) -> ENUM:
    return ENUM(py_enum, name=name, create_type=False, values_callable=_values)


technical_condition_enum = _enum(TechnicalCondition, "vehicle_technical_condition")
qualification_kind_enum = _enum(QualificationKind, "personnel_qualification_kind")
assignment_status_enum = _enum(AssignmentStatus, "resource_assignment_status")
resource_event_enum = _enum(ResourceEventType, "resource_event_type")

NEW_ENUMS = (
    technical_condition_enum,
    qualification_kind_enum,
    assignment_status_enum,
    resource_event_enum,
)

__all__ = [
    "NEW_ENUMS",
    "assignment_status_enum",
    "qualification_kind_enum",
    "resource_event_enum",
    "technical_condition_enum",
]
