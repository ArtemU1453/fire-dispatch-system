"""Call-management dependency providers (Dependency Injection wiring).

The telephony ``CallProvider`` is a process-wide singleton so a call's provider
handle survives across requests (the ``MockCallProvider`` keeps its state in
memory). Swapping in a real backend later is a one-line change here.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.deps import SessionDep
from app.calls.providers import CallProvider, MockCallProvider
from app.calls.services import CallService

# One shared provider for the whole process (see module docstring).
_provider: CallProvider = MockCallProvider()


def get_call_provider() -> CallProvider:
    return _provider


CallProviderDep = Annotated[CallProvider, Depends(get_call_provider)]


def get_call_service(
    session: SessionDep, provider: CallProviderDep
) -> CallService:
    return CallService(session, provider=provider)


CallServiceDep = Annotated[CallService, Depends(get_call_service)]
