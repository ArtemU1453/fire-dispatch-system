"""Built-in push providers (Stage 19).

No real push vendor is bundled (per the "don't tie to a provider" constraint).
``LogPushProvider`` records what *would* be sent — useful for development, tests
and auditing — and ``NullPushProvider`` silently drops messages. A real provider
implements the same :class:`PushProvider` interface and is injected via config.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.mobile.push.base import Device, PushMessage, PushProvider


@dataclass
class SentRecord:
    token: str
    user_id: str
    message: dict


class LogPushProvider(PushProvider):
    """Records delivered messages in memory instead of calling a vendor."""

    name = "log"

    def __init__(self) -> None:
        self.sent: list[SentRecord] = []

    def send(self, device: Device, message: PushMessage) -> bool:
        self.sent.append(
            SentRecord(
                token=device.token, user_id=device.user_id, message=message.to_dict()
            )
        )
        return True


class NullPushProvider(PushProvider):
    """Silently drops messages (e.g. push disabled)."""

    name = "null"

    def send(self, device: Device, message: PushMessage) -> bool:
        return True
