"""``MockAIProvider`` — an offline, deterministic AI provider for this stage.

It fully implements the :class:`AIProvider` interface using the keyword / regex
heuristics in :mod:`app.ai.utils.text_analysis`. No network, no ML, no external
API — so the whole AI platform (transcription → extraction → classification →
summary → analysis) can be exercised in tests and development, and stands in
until a real provider (OpenAI / Azure / local LLM / ASR model) is connected.

Every result is stamped with an :class:`AIResultMeta` (provider, model, version,
confidence, processing time).
"""

from __future__ import annotations

from app.ai.interfaces.provider import AIProvider
from app.ai.interfaces.results import (
    AICapability,
    AIResultMeta,
    AnalysisResult,
    ClassificationResult,
    EntityExtractionResult,
    ExtractedEntities,
    ProviderHealth,
    SummaryResult,
    TranscriptionResult,
    TranscriptSegment,
)
from app.ai.utils.text_analysis import (
    TextAnalysis,
    analyze_text,
    estimate_confidence,
)
from app.ai.utils.timing import Stopwatch

_SAMPLE_TRANSCRIPT = (
    "Здравствуйте, у нас пожар в многоквартирном жилом доме по адресу "
    "улица Ленина, дом 10, квартира 5. Возможно, внутри есть люди. "
    "Меня зовут Иван Петров, телефон +7 999 123 45 67."
)


class MockAIProvider(AIProvider):
    """Deterministic, offline implementation of ``AIProvider``."""

    name = "mock"
    model = "mock-dispatch-nlp"
    model_version = "1.0.0"
    capabilities = (
        AICapability.TRANSCRIBE,
        AICapability.EXTRACT_ENTITIES,
        AICapability.CLASSIFY_INCIDENT,
        AICapability.SUMMARIZE,
        AICapability.ANALYZE,
    )

    def _meta(self, confidence: float, elapsed_ms: int) -> AIResultMeta:
        return AIResultMeta(
            provider=self.name,
            model=self.model,
            model_version=self.model_version,
            confidence=confidence,
            processing_ms=elapsed_ms,
        )

    async def transcribe(
        self,
        audio_ref: str | None,
        *,
        language: str | None = None,
        sample_text: str | None = None,
    ) -> TranscriptionResult:
        sw = Stopwatch()
        text = sample_text or _SAMPLE_TRANSCRIPT
        lang = language or "ru"
        # One naive segment per sentence, evenly spaced.
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        segments: list[TranscriptSegment] = []
        step = 3000
        for i, sentence in enumerate(sentences):
            segments.append(
                TranscriptSegment(
                    start_ms=i * step,
                    end_ms=(i + 1) * step,
                    text=sentence,
                    confidence=0.92,
                )
            )
        return TranscriptionResult(
            text=text, language=lang, confidence=0.92, segments=segments,
            meta=self._meta(0.92, sw.elapsed_ms()),
        )

    async def extract_entities(
        self, text: str, *, language: str = "ru"
    ) -> EntityExtractionResult:
        sw = Stopwatch()
        analysis = analyze_text(text)
        entities = self._entities(analysis)
        return EntityExtractionResult(
            entities=entities,
            meta=self._meta(estimate_confidence(analysis), sw.elapsed_ms()),
        )

    async def classify_incident(
        self, text: str, *, language: str = "ru"
    ) -> ClassificationResult:
        sw = Stopwatch()
        analysis = analyze_text(text)
        return self._classification(analysis, sw.elapsed_ms())

    async def summarize(
        self, text: str, *, language: str = "ru"
    ) -> SummaryResult:
        sw = Stopwatch()
        analysis = analyze_text(text)
        return SummaryResult(
            summary=self._summary(analysis),
            meta=self._meta(estimate_confidence(analysis), sw.elapsed_ms()),
        )

    async def analyze(
        self, text: str, *, language: str = "ru"
    ) -> AnalysisResult:
        sw = Stopwatch()
        analysis = analyze_text(text)
        return AnalysisResult(
            summary=self._summary(analysis),
            entities=self._entities(analysis),
            classification=self._classification(analysis, sw.elapsed_ms()),
            meta=self._meta(estimate_confidence(analysis), sw.elapsed_ms()),
        )

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            healthy=True, provider=self.name, models=[self.model],
            capabilities=list(self.capabilities),
            detail="offline deterministic provider",
        )

    # ------------------------------------------------------------ helpers
    @staticmethod
    def _entities(analysis: TextAnalysis) -> ExtractedEntities:
        extra: dict[str, str] = {}
        if analysis.people_inside:
            extra["people_inside"] = "true"
        if analysis.matched_keywords:
            extra["keywords"] = ", ".join(analysis.matched_keywords)
        return ExtractedEntities(
            address=analysis.address,
            incident_type=analysis.incident_type_name,
            category=analysis.category,
            objects=analysis.objects,
            phone=analysis.phone,
            reporter_name=analysis.reporter_name,
            extra=extra,
        )

    def _classification(
        self, analysis: TextAnalysis, elapsed_ms: int
    ) -> ClassificationResult:
        return ClassificationResult(
            incident_type_code=analysis.incident_type_code,
            incident_type_name=analysis.incident_type_name,
            category=analysis.category,
            priority=analysis.priority,
            meta=self._meta(estimate_confidence(analysis), elapsed_ms),
        )

    @staticmethod
    def _summary(analysis: TextAnalysis) -> str:
        kind = analysis.incident_type_name or "Происшествие"
        where = ""
        if analysis.objects:
            where = f" в объекте типа «{analysis.objects[0]}»"
        parts = [f"Сообщение: {kind.lower()}{where}."]
        if analysis.people_inside:
            parts.append("Возможны люди внутри.")
        if analysis.address:
            parts.append(f"Адрес: {analysis.address}.")
        else:
            parts.append("Адрес не определён.")
        return " ".join(parts)
