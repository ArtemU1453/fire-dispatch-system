"""Telephony providers (the ``CallProvider`` seam)."""

from __future__ import annotations

from app.calls.providers.base import (
    CallProvider,
    ProviderCall,
    ProviderCallState,
    ProviderHealth,
)
from app.calls.providers.mock import MockCallProvider

__all__ = [
    "CallProvider",
    "MockCallProvider",
    "ProviderCall",
    "ProviderCallState",
    "ProviderHealth",
]
