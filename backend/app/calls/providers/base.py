"""The ``CallProvider`` interface — the telephony seam.

Telephony is **not** implemented at this stage. Instead, all interaction with a
phone platform goes through this abstract interface, so a real backend
(Asterisk, FreeSWITCH, a SIP trunk, WebRTC, …) can be plugged in later **without
changing** the call service or the rest of the system.

The only concrete implementation now is :class:`MockCallProvider`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from app.calls.models.enums import CallDirection, CallSource


class ProviderCallState(str, Enum):
    """The state of a call as reported by the telephony provider."""

    RINGING = "ringing"
    ANSWERED = "answered"
    HELD = "held"
    TRANSFERRED = "transferred"
    ENDED = "ended"
    FAILED = "failed"


@dataclass(slots=True)
class ProviderCall:
    """A telephony-side call handle returned by a :class:`CallProvider`.

    This is deliberately transport-agnostic: it carries only what the call
    service needs to create / update a :class:`~app.calls.models.entities.Call`.
    """

    external_id: str
    state: ProviderCallState
    caller_number: str | None = None
    callee_number: str | None = None
    direction: CallDirection = CallDirection.INBOUND
    source: CallSource = CallSource.PHONE
    started_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    answered_at: datetime | None = None
    ended_at: datetime | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ProviderHealth:
    healthy: bool
    provider: str
    detail: str | None = None


class CallProvider(ABC):
    """Abstract telephony provider.

    Implementations wrap a concrete platform. Every method is async so a real
    provider can perform network I/O; the mock returns immediately.
    """

    name: str = "base"

    @abstractmethod
    async def receive_call(
        self,
        *,
        caller_number: str | None = None,
        callee_number: str | None = None,
        direction: CallDirection = CallDirection.INBOUND,
        source: CallSource = CallSource.PHONE,
        meta: dict[str, Any] | None = None,
    ) -> ProviderCall:
        """Register an incoming call and return its telephony handle."""

    @abstractmethod
    async def answer_call(self, external_id: str) -> ProviderCall:
        """Answer (pick up) a ringing call."""

    @abstractmethod
    async def end_call(self, external_id: str) -> ProviderCall:
        """Hang up a call."""

    @abstractmethod
    async def hold_call(self, external_id: str) -> ProviderCall:
        """Put a call on hold."""

    @abstractmethod
    async def transfer_call(
        self, external_id: str, *, destination: str
    ) -> ProviderCall:
        """Transfer a call to another destination."""

    @abstractmethod
    async def health_check(self) -> ProviderHealth:
        """Report whether the provider is reachable / operational."""


def new_external_id() -> str:
    """A synthetic provider-side call id (used by the mock)."""
    return f"mock-{uuid4().hex[:12]}"
