"""Shared PostgreSQL enum type objects for the incidents module.

Follows the project convention: one ``ENUM`` per type name, ``values_callable``
(lowercase value-labels) and ``create_type=False`` — the new types are created and
dropped exactly once by the incidents migration.
"""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy.dialects.postgresql import ENUM

from app.incidents.models.enums import (
    AttachmentKind,
    ChangeSource,
    DispatchUnitStatus,
    IncidentCategory,
    IncidentPriority,
    IncidentSource,
    IncidentStatus,
    TimelineEventType,
)


def _values(enum_cls: Iterable) -> list[str]:
    return [member.value for member in enum_cls]


def _enum(py_enum, name: str) -> ENUM:
    return ENUM(py_enum, name=name, create_type=False, values_callable=_values)


incident_status_enum = _enum(IncidentStatus, "incident_status")
incident_priority_enum = _enum(IncidentPriority, "incident_priority")
incident_category_enum = _enum(IncidentCategory, "incident_category")
incident_source_enum = _enum(IncidentSource, "incident_source")
timeline_event_enum = _enum(TimelineEventType, "incident_timeline_event")
change_source_enum = _enum(ChangeSource, "incident_change_source")
dispatch_unit_status_enum = _enum(DispatchUnitStatus, "incident_dispatch_status")
attachment_kind_enum = _enum(AttachmentKind, "incident_attachment_kind")

# All new enum types managed explicitly by the incidents migration.
NEW_ENUMS = (
    incident_status_enum,
    incident_priority_enum,
    incident_category_enum,
    incident_source_enum,
    timeline_event_enum,
    change_source_enum,
    dispatch_unit_status_enum,
    attachment_kind_enum,
)

__all__ = [
    "NEW_ENUMS",
    "attachment_kind_enum",
    "change_source_enum",
    "dispatch_unit_status_enum",
    "incident_category_enum",
    "incident_priority_enum",
    "incident_source_enum",
    "incident_status_enum",
    "timeline_event_enum",
]
