"""EntityExtractionService (stage §5).

Extracts address, incident type, likely category, mentioned objects, phone,
reporter name and additional signals from a conversation, and returns them as a
**suggestion for the dispatcher**. It never reads or writes any Incident field —
the result is advisory only.
"""

from __future__ import annotations

from uuid import UUID

from app.ai.interfaces.results import EntityExtractionResult
from app.ai.models.enums import AIAuditCapability
from app.ai.services.base import AIServiceBase


class EntityExtractionService(AIServiceBase):
    async def extract(
        self,
        text: str,
        *,
        language: str = "ru",
        provider: str | None = None,
        call_id: UUID | None = None,
        incident_id: UUID | None = None,
    ) -> EntityExtractionResult:
        prov = self.provider(provider)
        return await self._run(
            AIAuditCapability.EXTRACT_ENTITIES,
            prov,
            prov.extract_entities(text, language=language),
            meta_of=lambda r: r.meta,
            language=language,
            call_id=call_id,
            incident_id=incident_id,
        )
