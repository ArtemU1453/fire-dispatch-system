"""Integration tests for AI services + audit + pipeline (require PostgreSQL)."""

from __future__ import annotations

from uuid import UUID

import pytest

from app.ai.interfaces.results import AnalysisResult
from app.ai.models.enums import AIAuditCapability, AIAuditStatus
from app.ai.pipelines import CallAnalysisPipeline
from app.ai.providers import MockAIProvider
from app.ai.providers.registry import AIProviderRegistry
from app.ai.repositories import AIAuditRepository
from app.ai.services import (
    AnalysisService,
    ClassificationService,
    EntityExtractionService,
    SummaryService,
    TranscriptionService,
)
from app.calls.models.entities import Call
from app.core.exceptions import ValidationError

from .conftest import PREFIX, AISeed

pytestmark = pytest.mark.asyncio


async def test_extraction_service_writes_audit(pg_factory, seed: AISeed) -> None:
    async with pg_factory() as s:
        service = EntityExtractionService(s)
        result = await service.extract(
            seed.call_text, call_id=UUID(seed.call_id),
            incident_id=UUID(seed.incident_id),
        )
        assert result.entities.phone == "+7 999 123 45 67"
        assert result.meta.provider == "mock"
        await s.commit()

    async with pg_factory() as s:
        rows = await AIAuditRepository(s).list_entries(
            capability=AIAuditCapability.EXTRACT_ENTITIES
        )
        entry = next(r for r in rows if str(r.call_id) == seed.call_id)
        assert entry.status is AIAuditStatus.SUCCESS
        assert entry.provider == "mock"
        assert entry.model_version == "1.0.0"
        assert entry.confidence is not None
        assert entry.latency_ms is not None
        assert str(entry.incident_id) == seed.incident_id


async def test_classification_service(pg_factory, seed: AISeed) -> None:
    async with pg_factory() as s:
        result = await ClassificationService(s).classify(seed.call_text)
        assert result.category == "fire"
        assert result.priority == "critical"
        await s.commit()

    async with pg_factory() as s:
        rows = await AIAuditRepository(s).list_entries(
            capability=AIAuditCapability.CLASSIFY_INCIDENT
        )
        assert any(r.status is AIAuditStatus.SUCCESS for r in rows)


async def test_summary_service(pg_factory, seed: AISeed) -> None:
    async with pg_factory() as s:
        result = await SummaryService(s).summarize(seed.call_text)
        assert "пожар" in result.summary.lower()
        await s.commit()


async def test_transcription_service(pg_factory, seed: AISeed) -> None:
    async with pg_factory() as s:
        result = await TranscriptionService(s).transcribe(
            "audio://ref", sample_text=seed.call_text, call_id=UUID(seed.call_id)
        )
        assert result.text == seed.call_text
        assert result.segments
        await s.commit()

    async with pg_factory() as s:
        rows = await AIAuditRepository(s).list_entries(
            capability=AIAuditCapability.TRANSCRIBE
        )
        assert any(str(r.call_id) == seed.call_id for r in rows)


async def test_analysis_service_bundle(pg_factory, seed: AISeed) -> None:
    async with pg_factory() as s:
        result = await AnalysisService(s).analyze(seed.call_text)
        assert isinstance(result, AnalysisResult)
        assert result.entities.address is not None
        assert result.classification.category == "fire"
        await s.commit()


async def test_call_analysis_pipeline(pg_factory, seed: AISeed) -> None:
    async with pg_factory() as s:
        pipeline = CallAnalysisPipeline(s)
        result = await pipeline.analyze_call(UUID(seed.call_id))
        assert result.classification.category == "fire"
        assert result.entities.phone == "+7 999 123 45 67"
        await s.commit()

    async with pg_factory() as s:
        rows = await AIAuditRepository(s).list_entries(
            capability=AIAuditCapability.ANALYZE, call_id=UUID(seed.call_id)
        )
        assert rows and rows[0].status is AIAuditStatus.SUCCESS


async def test_pipeline_requires_text(pg_factory, seed: AISeed) -> None:
    async with pg_factory() as s:
        empty = Call(number=f"{PREFIX}-EMPTY")  # no transcript, no notes
        s.add(empty)
        await s.flush()
        empty_id = empty.id
        await s.commit()

    async with pg_factory() as s:
        pipeline = CallAnalysisPipeline(s)
        with pytest.raises(ValidationError):
            await pipeline.analyze_call(empty_id)


class _FailingProvider(MockAIProvider):
    name = "failing"

    async def analyze(self, text: str, *, language: str = "ru"):
        raise RuntimeError("provider exploded")


async def test_error_is_audited_and_reraised(pg_factory, seed: AISeed) -> None:
    registry = AIProviderRegistry()
    registry.register(_FailingProvider(), default=True)
    async with pg_factory() as s:
        service = AnalysisService(s, registry=registry)
        with pytest.raises(RuntimeError):
            await service.analyze(seed.call_text, call_id=UUID(seed.call_id))
        await s.commit()

    async with pg_factory() as s:
        rows = await AIAuditRepository(s).list_entries(provider="failing")
        assert rows
        entry = rows[0]
        assert entry.status is AIAuditStatus.ERROR
        assert entry.error and "exploded" in entry.error
