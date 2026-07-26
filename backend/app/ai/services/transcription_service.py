"""TranscriptionService (stage §4) — speech-to-text through the AI interface.

Interface + mock only at this stage. Supports recognised text, language,
temporal segments and recognition confidence. Swapping in a real ASR model
(a specialised speech-recognition provider) requires no change here.
"""

from __future__ import annotations

from uuid import UUID

from app.ai.interfaces.results import TranscriptionResult
from app.ai.models.enums import AIAuditCapability
from app.ai.services.base import AIServiceBase


class TranscriptionService(AIServiceBase):
    async def transcribe(
        self,
        audio_ref: str | None,
        *,
        language: str | None = None,
        sample_text: str | None = None,
        provider: str | None = None,
        call_id: UUID | None = None,
    ) -> TranscriptionResult:
        prov = self.provider(provider)
        return await self._run(
            AIAuditCapability.TRANSCRIBE,
            prov,
            prov.transcribe(
                audio_ref, language=language, sample_text=sample_text
            ),
            meta_of=lambda r: r.meta,
            language=language,
            call_id=call_id,
        )
