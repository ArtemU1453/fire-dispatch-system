"""AI audit recorder (stage §12).

Persists **metadata only** about each AI invocation — provider, model, version,
capability, success / error, confidence, processing time and response latency,
plus the related call / incident. **Prompts and conversation text are never
stored** here, per the security / data-retention requirement.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.interfaces.results import AIResultMeta
from app.ai.models.entities import AIAuditLog
from app.ai.models.enums import AIAuditCapability, AIAuditStatus


class AIAuditRecorder:
    """Writes AI audit entries on the session (the caller owns the commit)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def record_success(
        self,
        capability: AIAuditCapability,
        meta: AIResultMeta,
        *,
        latency_ms: int,
        language: str | None = None,
        call_id: UUID | None = None,
        incident_id: UUID | None = None,
        extra: dict | None = None,
    ) -> AIAuditLog:
        entry = AIAuditLog(
            capability=capability,
            status=AIAuditStatus.SUCCESS,
            provider=meta.provider,
            model=meta.model,
            model_version=meta.model_version,
            confidence=meta.confidence,
            processing_ms=meta.processing_ms,
            latency_ms=latency_ms,
            language=language,
            call_id=call_id,
            incident_id=incident_id,
            meta=extra,
        )
        self._session.add(entry)
        return entry

    def record_error(
        self,
        capability: AIAuditCapability,
        *,
        provider: str,
        model: str,
        model_version: str,
        error: str,
        latency_ms: int,
        language: str | None = None,
        call_id: UUID | None = None,
        incident_id: UUID | None = None,
    ) -> AIAuditLog:
        entry = AIAuditLog(
            capability=capability,
            status=AIAuditStatus.ERROR,
            provider=provider,
            model=model,
            model_version=model_version,
            error=error[:512],
            latency_ms=latency_ms,
            language=language,
            call_id=call_id,
            incident_id=incident_id,
        )
        self._session.add(entry)
        return entry
