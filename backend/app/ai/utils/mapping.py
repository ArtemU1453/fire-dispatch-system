"""Mapping between AI result dataclasses / ORM and API schemas."""

from __future__ import annotations

from app.ai.interfaces.provider import AIProvider
from app.ai.interfaces.results import (
    AIResultMeta,
    AnalysisResult,
    ClassificationResult,
    EntityExtractionResult,
    ExtractedEntities,
    ProviderHealth,
    SummaryResult,
    TranscriptionResult,
)
from app.ai.models.entities import AIAuditLog
from app.ai.schemas.ai import (
    AIAuditResponse,
    AIProviderInfo,
    AnalysisResponse,
    ClassificationResponse,
    EntityExtractionResponse,
    ExtractedEntitiesSchema,
    SummaryResponse,
    TranscriptionResponse,
    TranscriptSegmentSchema,
)
from app.ai.schemas.ai import (
    AIResultMeta as AIResultMetaSchema,
)


def meta_to_schema(meta: AIResultMeta | None) -> AIResultMetaSchema | None:
    if meta is None:
        return None
    return AIResultMetaSchema(
        provider=meta.provider,
        model=meta.model,
        model_version=meta.model_version,
        confidence=meta.confidence,
        processing_ms=meta.processing_ms,
    )


def transcription_to_response(result: TranscriptionResult) -> TranscriptionResponse:
    return TranscriptionResponse(
        text=result.text,
        language=result.language,
        confidence=result.confidence,
        segments=[
            TranscriptSegmentSchema(
                start_ms=s.start_ms, end_ms=s.end_ms, text=s.text,
                confidence=s.confidence,
            )
            for s in result.segments
        ],
        meta=meta_to_schema(result.meta),
    )


def entities_to_schema(entities: ExtractedEntities) -> ExtractedEntitiesSchema:
    return ExtractedEntitiesSchema(
        address=entities.address,
        incident_type=entities.incident_type,
        category=entities.category,
        objects=list(entities.objects),
        phone=entities.phone,
        reporter_name=entities.reporter_name,
        extra=dict(entities.extra),
    )


def extraction_to_response(
    result: EntityExtractionResult,
) -> EntityExtractionResponse:
    return EntityExtractionResponse(
        entities=entities_to_schema(result.entities),
        meta=meta_to_schema(result.meta),
    )


def classification_to_response(
    result: ClassificationResult,
) -> ClassificationResponse:
    return ClassificationResponse(
        incident_type_code=result.incident_type_code,
        incident_type_name=result.incident_type_name,
        category=result.category,
        priority=result.priority,
        meta=meta_to_schema(result.meta),
    )


def summary_to_response(result: SummaryResult) -> SummaryResponse:
    return SummaryResponse(
        summary=result.summary, meta=meta_to_schema(result.meta)
    )


def analysis_to_response(result: AnalysisResult) -> AnalysisResponse:
    return AnalysisResponse(
        summary=result.summary,
        entities=entities_to_schema(result.entities),
        classification=classification_to_response(result.classification),
        meta=meta_to_schema(result.meta),
    )


def provider_info(
    provider: AIProvider, *, health: ProviderHealth, is_default: bool
) -> AIProviderInfo:
    return AIProviderInfo(
        name=provider.name,
        model=provider.model,
        model_version=provider.model_version,
        capabilities=[c.value for c in provider.capabilities],
        healthy=health.healthy,
        is_default=is_default,
    )


def audit_to_response(entry: AIAuditLog) -> AIAuditResponse:
    return AIAuditResponse.model_validate(entry)
