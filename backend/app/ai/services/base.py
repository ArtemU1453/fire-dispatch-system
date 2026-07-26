"""Shared plumbing for AI services.

Every capability service resolves a provider from the registry, runs it behind
the unified interface, measures latency, and writes an audit entry (success or
error). Keeping this in one place means each concrete service (transcription,
extraction, classification, summary) stays tiny and swapping the model changes
nothing here.
"""

from __future__ import annotations

from collections.abc import Awaitable
from typing import TypeVar
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.interfaces.provider import AIProvider
from app.ai.models.enums import AIAuditCapability
from app.ai.providers.registry import AIProviderRegistry, default_registry
from app.ai.services.audit import AIAuditRecorder
from app.ai.utils.timing import Stopwatch

T = TypeVar("T")


class AIServiceBase:
    """Base for capability services: provider resolution + audited execution."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        registry: AIProviderRegistry | None = None,
    ) -> None:
        self._session = session
        self._registry = registry or default_registry()
        self._audit = AIAuditRecorder(session)

    def provider(self, name: str | None = None) -> AIProvider:
        return self._registry.get(name)

    async def _run(
        self,
        capability: AIAuditCapability,
        provider: AIProvider,
        awaitable: Awaitable[T],
        *,
        meta_of,
        language: str | None = None,
        call_id: UUID | None = None,
        incident_id: UUID | None = None,
        extra: dict | None = None,
    ) -> T:
        """Execute a provider call, timing it and writing an audit entry."""
        sw = Stopwatch()
        try:
            result = await awaitable
        except Exception as exc:  # noqa: BLE001 - audited then re-raised
            self._audit.record_error(
                capability,
                provider=provider.name,
                model=provider.model,
                model_version=provider.model_version,
                error=str(exc),
                latency_ms=sw.elapsed_ms(),
                language=language,
                call_id=call_id,
                incident_id=incident_id,
            )
            await self._session.flush()
            raise
        self._audit.record_success(
            capability,
            meta_of(result),
            latency_ms=sw.elapsed_ms(),
            language=language,
            call_id=call_id,
            incident_id=incident_id,
            extra=extra,
        )
        await self._session.flush()
        return result
