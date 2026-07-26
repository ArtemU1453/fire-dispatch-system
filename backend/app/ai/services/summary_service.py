"""SummaryService (stage §7) — a short human-readable summary of the call."""

from __future__ import annotations

from uuid import UUID

from app.ai.interfaces.results import SummaryResult
from app.ai.models.enums import AIAuditCapability
from app.ai.services.base import AIServiceBase


class SummaryService(AIServiceBase):
    async def summarize(
        self,
        text: str,
        *,
        language: str = "ru",
        provider: str | None = None,
        call_id: UUID | None = None,
        incident_id: UUID | None = None,
    ) -> SummaryResult:
        prov = self.provider(provider)
        return await self._run(
            AIAuditCapability.SUMMARIZE,
            prov,
            prov.summarize(text, language=language),
            meta_of=lambda r: r.meta,
            language=language,
            call_id=call_id,
            incident_id=incident_id,
        )
