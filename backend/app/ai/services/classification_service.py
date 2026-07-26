"""ClassificationService (stage §6).

Suggests an incident type, category and priority for a conversation. All outputs
are **recommendations** — the dispatcher decides, and nothing is applied
automatically.
"""

from __future__ import annotations

from uuid import UUID

from app.ai.interfaces.results import ClassificationResult
from app.ai.models.enums import AIAuditCapability
from app.ai.services.base import AIServiceBase


class ClassificationService(AIServiceBase):
    async def classify(
        self,
        text: str,
        *,
        language: str = "ru",
        provider: str | None = None,
        call_id: UUID | None = None,
        incident_id: UUID | None = None,
    ) -> ClassificationResult:
        prov = self.provider(provider)
        return await self._run(
            AIAuditCapability.CLASSIFY_INCIDENT,
            prov,
            prov.classify_incident(text, language=language),
            meta_of=lambda r: r.meta,
            language=language,
            call_id=call_id,
            incident_id=incident_id,
        )
