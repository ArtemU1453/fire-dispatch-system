"""Enumerations for the incident-management module.

Value-labels are lowercase to match the project-wide value-based enum
serialization; the native PostgreSQL types are created explicitly in the
incidents migration.
"""

from __future__ import annotations

from enum import Enum


class IncidentStatus(str, Enum):
    """The lifecycle state of an incident (see the state machine)."""

    CREATED = "created"                     # Создано
    CHECKING = "checking"                   # Проверка информации
    CONFIRMED = "confirmed"                 # Подтверждено
    SELECTING = "selecting"                 # Подбор подразделений
    DISPATCH_CONFIRMED = "dispatch_confirmed"  # Подтверждение диспетчером
    DISPATCHED = "dispatched"               # Высылка подразделений
    ON_SCENE = "on_scene"                   # Работа на месте
    LOCALIZED = "localized"                 # Локализация
    LIQUIDATED = "liquidated"               # Ликвидация
    COMPLETED = "completed"                 # Завершено
    ARCHIVED = "archived"                   # Архив
    CANCELLED = "cancelled"                 # Отменено (до высылки)


class IncidentPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentCategory(str, Enum):
    """Broad classification of the incident."""

    FIRE = "fire"
    ROAD_ACCIDENT = "road_accident"
    RESCUE = "rescue"
    CHEMICAL = "chemical"
    WILDFIRE = "wildfire"
    FALSE_ALARM = "false_alarm"
    SPECIAL_OPS = "special_ops"
    SERVICE_OPS = "service_ops"
    OTHER = "other"


class IncidentSource(str, Enum):
    """How the report reached the dispatcher."""

    PHONE = "phone"
    RADIO = "radio"
    SYSTEM = "system"
    PATROL = "patrol"
    MANUAL = "manual"
    OTHER = "other"


class TimelineEventType(str, Enum):
    """Chronology event kinds recorded on the incident timeline."""

    CREATED = "created"
    INFO_CHECKED = "info_checked"
    CONFIRMED = "confirmed"
    ADDRESS_CHANGED = "address_changed"
    CATEGORY_CHANGED = "category_changed"
    PRIORITY_CHANGED = "priority_changed"
    RECOMMENDATION_REQUESTED = "recommendation_requested"
    UNITS_ASSIGNED = "units_assigned"
    STATUS_CHANGED = "status_changed"
    COMMENT_ADDED = "comment_added"
    ATTACHMENT_ADDED = "attachment_added"
    PARTICIPANT_ADDED = "participant_added"
    CLOSED = "closed"
    ARCHIVED = "archived"


class ChangeSource(str, Enum):
    """Origin of a field change (for the audit history)."""

    DISPATCHER = "dispatcher"
    SYSTEM = "system"
    INTEGRATION = "integration"


class DispatchUnitStatus(str, Enum):
    """Status of a unit assigned to an incident."""

    ASSIGNED = "assigned"
    EN_ROUTE = "en_route"
    ON_SCENE = "on_scene"
    RETURNING = "returning"
    RELEASED = "released"
    CANCELLED = "cancelled"


class AttachmentKind(str, Enum):
    PHOTO = "photo"
    DOCUMENT = "document"
    SCHEME = "scheme"
    OTHER = "other"
