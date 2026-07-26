"""Enumerations for the call-management module.

Value-labels are lowercase to match the project-wide value-based enum
serialization; the native PostgreSQL types are created explicitly in the calls
migration.
"""

from __future__ import annotations

from enum import Enum


class CallStatus(str, Enum):
    """The lifecycle state of a call (see the state machine)."""

    NEW = "new"                # Новый
    RINGING = "ringing"        # Ожидает ответа
    ACCEPTED = "accepted"      # Принят
    IN_PROGRESS = "in_progress"  # В обработке
    LINKED = "linked"          # Связан с Incident
    COMPLETED = "completed"    # Завершён
    CANCELLED = "cancelled"    # Отменён
    ERROR = "error"            # Ошибка


class CallPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class CallType(str, Enum):
    """What kind of call this is."""

    EMERGENCY = "emergency"      # Экстренный вызов
    SERVICE = "service"          # Служебный
    INFORMATION = "information"  # Справочный
    TEST = "test"                # Проверочный
    CALLBACK = "callback"        # Обратный вызов
    OTHER = "other"


class CallSource(str, Enum):
    """How the call reached the system (the telephony channel)."""

    PHONE = "phone"
    MOBILE = "mobile"
    SIP = "sip"
    WEBRTC = "webrtc"
    RADIO = "radio"
    MANUAL = "manual"      # dispatcher entered it by hand
    OTHER = "other"


class CallDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class CallEventType(str, Enum):
    """History event kinds recorded for a call (append-only)."""

    CREATED = "created"
    STATUS_CHANGED = "status_changed"
    QUEUED = "queued"
    DEQUEUED = "dequeued"
    DISPATCHER_ASSIGNED = "dispatcher_assigned"
    ANSWERED = "answered"
    INCIDENT_CREATED = "incident_created"
    INCIDENT_LINKED = "incident_linked"
    PARTICIPANT_ADDED = "participant_added"
    RECORDING_REGISTERED = "recording_registered"
    TRANSCRIPT_REGISTERED = "transcript_registered"
    PROVIDER_ACTION = "provider_action"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class CallQueueStatus(str, Enum):
    """Lifecycle of a queue entry."""

    WAITING = "waiting"        # Ожидает свободного диспетчера
    ASSIGNED = "assigned"      # Назначен диспетчер
    IN_PROGRESS = "in_progress"  # В обработке
    DONE = "done"              # Обработан / убран из очереди
    ABANDONED = "abandoned"    # Оставлен (не дождались ответа)


class CallParticipantRole(str, Enum):
    CALLER = "caller"
    DISPATCHER = "dispatcher"
    TRANSFERRED = "transferred"
    OBSERVER = "observer"
    OTHER = "other"


class CallRecordingStatus(str, Enum):
    """Processing status of a call recording (architecture only for now)."""

    PENDING = "pending"
    AVAILABLE = "available"
    PROCESSING = "processing"
    FAILED = "failed"
    DELETED = "deleted"


class CallTranscriptStatus(str, Enum):
    """Processing status of a call transcript (architecture only for now)."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CallLinkType(str, Enum):
    """How a call is linked to an incident."""

    CREATED = "created"   # the call created a new incident
    LINKED = "linked"     # the call was attached to an existing incident
