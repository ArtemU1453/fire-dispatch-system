"""PushService — device registry and event dispatch (Stage 19).

Registers devices per user and turns domain events (new/changed incident, route
change, new message, critical event) into :class:`PushMessage`s delivered
through the configured :class:`PushProvider`. Vendor-neutral; in-memory registry
(training/BFF state, no production DB).
"""

from __future__ import annotations

from app.mobile.push.base import Device, PushEventType, PushMessage, PushProvider
from app.mobile.push.providers import LogPushProvider


class PushService:
    def __init__(self, provider: PushProvider | None = None) -> None:
        self._provider: PushProvider = provider or LogPushProvider()
        self._devices: dict[str, Device] = {}     # token -> Device

    # --------------------------------------------------------------- devices
    def register(self, device: Device) -> Device:
        self._devices[device.token] = device
        return device

    def unregister(self, token: str) -> bool:
        return self._devices.pop(token, None) is not None

    def devices_for(self, user_id: str) -> list[Device]:
        return [d for d in self._devices.values() if d.user_id == user_id]

    @property
    def provider(self) -> PushProvider:
        return self._provider

    # ------------------------------------------------------------- dispatch
    def _dispatch(
        self, message: PushMessage, *, user_ids: list[str] | None = None
    ) -> int:
        targets = (
            [d for d in self._devices.values() if d.user_id in set(user_ids)]
            if user_ids is not None
            else list(self._devices.values())
        )
        delivered = 0
        for device in targets:
            if self._provider.send(device, message):
                delivered += 1
        return delivered

    # -------------------------------------------------------------- events
    def notify_new_incident(
        self, incident_id: str, summary: str, *, user_ids: list[str] | None = None
    ) -> int:
        return self._dispatch(
            PushMessage(
                event=PushEventType.NEW_INCIDENT,
                title="Новое происшествие",
                body=summary,
                data={"incident_id": incident_id},
                priority="high",
            ),
            user_ids=user_ids,
        )

    def notify_incident_change(
        self, incident_id: str, summary: str, *, user_ids: list[str] | None = None
    ) -> int:
        return self._dispatch(
            PushMessage(
                event=PushEventType.INCIDENT_CHANGE,
                title="Изменение происшествия",
                body=summary,
                data={"incident_id": incident_id},
            ),
            user_ids=user_ids,
        )

    def notify_route_change(
        self, unit_id: str, incident_id: str, *, user_ids: list[str] | None = None
    ) -> int:
        return self._dispatch(
            PushMessage(
                event=PushEventType.ROUTE_CHANGE,
                title="Изменение маршрута",
                body="Маршрут обновлён",
                data={"unit_id": unit_id, "incident_id": incident_id},
                priority="high",
            ),
            user_ids=user_ids,
        )

    def notify_new_message(
        self, to_user_id: str, text: str, *, from_user: str = ""
    ) -> int:
        return self._dispatch(
            PushMessage(
                event=PushEventType.NEW_MESSAGE,
                title="Новое сообщение",
                body=text,
                data={"from": from_user},
            ),
            user_ids=[to_user_id],
        )

    def notify_critical(
        self, message_text: str, *, incident_id: str | None = None,
        user_ids: list[str] | None = None,
    ) -> int:
        return self._dispatch(
            PushMessage(
                event=PushEventType.CRITICAL,
                title="КРИТИЧЕСКОЕ СОБЫТИЕ",
                body=message_text,
                data={"incident_id": incident_id} if incident_id else {},
                priority="high",
            ),
            user_ids=user_ids,
        )
