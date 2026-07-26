"""AnalysisService — a combined analysis (summary + entities + classification).

Runs the provider's ``analyze`` once and returns a single suggestion bundle for
the dispatcher (stage §7/§9). Like every AI service, the result is advisory and
nothing is applied automatically.
"""

from __future__ import annotations

from uuid import UUID

from app.ai.interfaces.results import AnalysisResult
from app.ai.models.enums import AIAuditCapability
from app.ai.services.base import AIServiceBase


class AnalysisService(AIServiceBase):
    async def analyze(
        self,
        text: str,
        *,
        language: str = "ru",
        provider: str | None = None,
        call_id: UUID | None = None,
        incident_id: UUID | None = None,
    ) -> AnalysisResult:
        prov = self.provider(provider)
        return await self._run(
            AIAuditCapability.ANALYZE,
            prov,
            prov.analyze(text, language=language),
            meta_of=lambda r: r.meta,
            language=language,
            call_id=call_id,
            incident_id=incident_id,
        )
