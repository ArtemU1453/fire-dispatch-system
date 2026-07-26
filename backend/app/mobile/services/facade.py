"""MobilePlatform facade — wires the BFF pieces together (Stage 19).

Holds the shared provider, push service, session store, commander and responder
services and the offline sync service, and registers the sync handlers. A single
instance backs the API; everything is in-memory (BFF state), so the mobile
platform never touches the production database.
"""

from __future__ import annotations

from app.mobile.providers.base import MobileDataProvider
from app.mobile.providers.sample import SampleDataProvider
from app.mobile.push.service import PushService
from app.mobile.security.tokens import SessionStore
from app.mobile.services.commander import CommanderService
from app.mobile.services.messages import MessageStore
from app.mobile.services.offline import SyncOperation, SyncResult, SyncService
from app.mobile.services.responder import ResponderService
from app.mobile.services.status import ResponderStateStore, ResponderStatus


class MobilePlatform:
    def __init__(self, provider: MobileDataProvider | None = None) -> None:
        self.provider: MobileDataProvider = provider or SampleDataProvider()
        self.push = PushService()
        self.sessions = SessionStore()
        self.status_store = ResponderStateStore()
        self.messages = MessageStore()
        self.commander = CommanderService(self.provider)
        self.responder = ResponderService(
            self.provider,
            status_store=self.status_store,
            messages=self.messages,
            push=self.push,
        )
        self.sync = SyncService()
        self._register_sync_handlers()

    def _register_sync_handlers(self) -> None:
        def _apply_status(payload: dict) -> dict:
            unit_id = str(payload["unit_id"])
            target = ResponderStatus(payload["status"])
            new = self.responder.update_status(unit_id, target)
            return {"unit_id": unit_id, "status": new.value}

        def _apply_message(payload: dict) -> dict:
            msg = self.responder.send_message(
                str(payload["unit_id"]),
                from_user=str(payload.get("from_user", payload["unit_id"])),
                text=str(payload["text"]),
                incident_id=payload.get("incident_id"),
            )
            return {"message_id": msg.id}

        self.sync.register("status", _apply_status)
        self.sync.register("message", _apply_message)

    def process_sync(self, operations: list[SyncOperation]) -> list[SyncResult]:
        return self.sync.process(operations)
