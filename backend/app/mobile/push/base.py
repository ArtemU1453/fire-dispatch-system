"""Push-notification abstraction (Stage 19).

A vendor-neutral push architecture: the application builds :class:`PushMessage`s
for well-defined events and hands them to a :class:`PushProvider`. Concrete
providers (FCM, APNs, a corporate gateway) implement the same interface and are
selected by configuration — nothing here is tied to a specific vendor.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Protocol


class PushEventType(str, enum.Enum):
    NEW_INCIDENT = "new_incident"
    INCIDENT_CHANGE = "incident_change"
    ROUTE_CHANGE = "route_change"
    NEW_MESSAGE = "new_message"
    CRITICAL = "critical"


@dataclass
class Device:
    """A registered device that can receive push messages."""

    token: str
    user_id: str
    platform: str = "unknown"        # ios | android | web | unknown
    app: str = "responder"           # commander | responder


@dataclass
class PushMessage:
    event: PushEventType
    title: str
    body: str
    data: dict[str, Any] = field(default_factory=dict)
    priority: str = "normal"         # normal | high

    def to_dict(self) -> dict[str, Any]:
        return {
            "event": self.event.value,
            "title": self.title,
            "body": self.body,
            "data": self.data,
            "priority": self.priority,
        }


class PushProvider(Protocol):
    """Delivers a message to a device token. Implementations are vendor-specific."""

    name: str

    def send(self, device: Device, message: PushMessage) -> bool: ...
