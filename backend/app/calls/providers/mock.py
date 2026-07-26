"""``MockCallProvider`` — an in-memory telephony provider for this stage.

It fully implements the :class:`CallProvider` interface without any real
telephony: calls are tracked in a dict and state transitions are simulated. This
lets the whole call-management flow (receive → answer → end, hold, transfer) be
exercised in tests and development, and stands in until a real SIP / Asterisk /
FreeSWITCH backend is connected.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.calls.models.enums import CallDirection, CallSource
from app.calls.providers.base import (
    CallProvider,
    ProviderCall,
    ProviderCallState,
    ProviderHealth,
    new_external_id,
)
from app.core.exceptions import NotFoundError


def _now() -> datetime:
    return datetime.now(tz=UTC)


class MockCallProvider(CallProvider):
    """A simple, deterministic in-memory implementation of ``CallProvider``."""

    name = "mock"

    def __init__(self) -> None:
        self._calls: dict[str, ProviderCall] = {}

    async def receive_call(
        self,
        *,
        caller_number: str | None = None,
        callee_number: str | None = None,
        direction: CallDirection = CallDirection.INBOUND,
        source: CallSource = CallSource.PHONE,
        meta: dict[str, Any] | None = None,
    ) -> ProviderCall:
        call = ProviderCall(
            external_id=new_external_id(),
            state=ProviderCallState.RINGING,
            caller_number=caller_number,
            callee_number=callee_number,
            direction=direction,
            source=source,
            started_at=_now(),
            meta=meta or {},
        )
        self._calls[call.external_id] = call
        return call

    async def answer_call(self, external_id: str) -> ProviderCall:
        call = self._get(external_id)
        call.state = ProviderCallState.ANSWERED
        call.answered_at = _now()
        return call

    async def end_call(self, external_id: str) -> ProviderCall:
        call = self._get(external_id)
        call.state = ProviderCallState.ENDED
        call.ended_at = _now()
        return call

    async def hold_call(self, external_id: str) -> ProviderCall:
        call = self._get(external_id)
        call.state = ProviderCallState.HELD
        return call

    async def transfer_call(
        self, external_id: str, *, destination: str
    ) -> ProviderCall:
        call = self._get(external_id)
        call.state = ProviderCallState.TRANSFERRED
        call.meta = {**call.meta, "transferred_to": destination}
        return call

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            healthy=True, provider=self.name,
            detail=f"{len(self._calls)} tracked call(s)",
        )

    def _get(self, external_id: str) -> ProviderCall:
        call = self._calls.get(external_id)
        if call is None:
            raise NotFoundError(f"Provider call not found: {external_id}")
        return call
