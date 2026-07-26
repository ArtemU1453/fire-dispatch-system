"""Responder service — field-unit operations (Stage 19).

Server-side logic for the Responder app: the dispatch card, the route, the
status state machine and short messages. The app only sends requests; the server
validates and decides (e.g. whether a status transition is allowed) and emits
push notifications.
"""

from __future__ import annotations

from app.mobile.providers.base import MobileDataProvider
from app.mobile.providers.types import DispatchCard, Route
from app.mobile.push.service import PushService
from app.mobile.services.messages import MessageStore, ServiceMessage
from app.mobile.services.status import ResponderStateStore, ResponderStatus


class ResponderError(ValueError):
    pass


class ResponderService:
    def __init__(
        self,
        provider: MobileDataProvider,
        *,
        status_store: ResponderStateStore | None = None,
        messages: MessageStore | None = None,
        push: PushService | None = None,
    ) -> None:
        self._provider = provider
        self._status = status_store or ResponderStateStore()
        self._messages = messages or MessageStore()
        self._push = push or PushService()

    # -------------------------------------------------------------- reads
    def dispatch(self, unit_id: str) -> DispatchCard:
        card = self._provider.get_dispatch(unit_id)
        if card is None:
            raise ResponderError(f"no active dispatch for unit {unit_id}")
        return card

    def route(self, unit_id: str) -> Route:
        route = self._provider.get_route(unit_id)
        if route is None:
            raise ResponderError(f"no route for unit {unit_id}")
        return route

    def current_status(self, unit_id: str) -> ResponderStatus:
        return self._status.current(unit_id)

    # ------------------------------------------------------------- status
    def update_status(
        self, unit_id: str, target: ResponderStatus
    ) -> ResponderStatus:
        # Transition is validated on the server (state machine decides).
        new_status = self._status.transition(unit_id, target)
        card = self._provider.get_dispatch(unit_id)
        if card is not None:
            self._push.notify_incident_change(
                card.incident_id,
                f"Подразделение {unit_id}: {new_status.value}",
            )
        return new_status

    # ------------------------------------------------------------ messages
    def send_message(
        self,
        unit_id: str,
        *,
        from_user: str,
        text: str,
        incident_id: str | None = None,
    ) -> ServiceMessage:
        if not text.strip():
            raise ResponderError("message text is empty")
        msg = self._messages.add(
            from_user=from_user, text=text, unit_id=unit_id,
            incident_id=incident_id,
        )
        # Notify command of the new field message.
        self._push.notify_new_message("command", msg.text, from_user=from_user)
        return msg

    def messages(self, unit_id: str) -> list[ServiceMessage]:
        return self._messages.list(unit_id=unit_id)

    @property
    def push(self) -> PushService:
        return self._push
