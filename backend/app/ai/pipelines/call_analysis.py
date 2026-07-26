"""Call-analysis pipeline — the Call Management integration (stage §9).

Given a call, it reads the call's transcript (or, failing that, the dispatcher's
notes) **without modifying the call**, runs the combined AI analysis and returns
a single suggestion bundle for the dispatcher — summary, extracted entities and a
suggested classification. The audit entry is linked to the call (and its incident
if one is attached).

**Nothing is applied automatically**: the pipeline only reads Call Management
data and produces advisory output. No Incident, resource, rule or status is
changed.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.interfaces.results import AnalysisResult
from app.ai.providers.registry import AIProviderRegistry
from app.ai.services.analysis_service import AnalysisService
from app.calls.services import CallService
from app.core.exceptions import ValidationError


class CallAnalysisPipeline:
    """Reads a call's text and produces an AI suggestion bundle (advisory)."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        registry: AIProviderRegistry | None = None,
    ) -> None:
        self._session = session
        self._calls = CallService(session)
        self._analysis = AnalysisService(session, registry=registry)

    async def analyze_call(
        self, call_id: UUID, *, provider: str | None = None
    ) -> AnalysisResult:
        call = await self._calls.get_call(call_id)  # 404 if missing (read-only)
        text = self._call_text(call)
        if not text:
            raise ValidationError(
                "Call has no transcript or notes to analyse"
            )
        return await self._analysis.analyze(
            text,
            provider=provider,
            call_id=call.id,
            incident_id=call.incident_id,
        )

    @staticmethod
    def _call_text(call) -> str | None:
        """The best available text for analysis (transcript, else notes)."""
        transcripts = [
            t for t in call.transcripts
            if not t.is_deleted and t.text_content
        ]
        if transcripts:
            # Prefer the most recent transcript.
            latest = max(transcripts, key=lambda t: t.created_at)
            return latest.text_content
        return call.notes
