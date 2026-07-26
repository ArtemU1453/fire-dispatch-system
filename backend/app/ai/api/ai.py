"""AI-platform REST endpoints (stage §10).

    POST /ai/transcribe · POST /ai/extract · POST /ai/classify
    POST /ai/summarize  · POST /ai/analyze  · POST /ai/calls/{id}/analyze
    GET  /ai/providers  · GET /ai/health    · GET /ai/audit

Every response is a **recommendation** for the dispatcher (`advisory=true`); the
platform never changes an incident, resource, rule or status.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query

from app.ai.deps import (
    AIAuditRepoDep,
    AIRegistryDep,
    AnalysisServiceDep,
    CallAnalysisPipelineDep,
    ClassificationServiceDep,
    EntityExtractionServiceDep,
    SummaryServiceDep,
    TranscriptionServiceDep,
)
from app.ai.models.enums import AIAuditCapability
from app.ai.schemas.ai import (
    AIAuditResponse,
    AIHealthResponse,
    AIProvidersResponse,
    AnalysisResponse,
    CallAnalysisRequest,
    ClassificationResponse,
    EntityExtractionResponse,
    SummaryResponse,
    TextRequest,
    TranscriptionRequest,
    TranscriptionResponse,
)
from app.ai.utils.mapping import (
    analysis_to_response,
    audit_to_response,
    classification_to_response,
    extraction_to_response,
    provider_info,
    summary_to_response,
    transcription_to_response,
)

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post(
    "/transcribe", response_model=TranscriptionResponse, summary="Transcribe audio"
)
async def transcribe(
    service: TranscriptionServiceDep, data: TranscriptionRequest
) -> TranscriptionResponse:
    result = await service.transcribe(
        data.audio_ref, language=data.language,
        sample_text=data.sample_text, provider=data.provider,
        call_id=data.call_id,
    )
    return transcription_to_response(result)


@router.post(
    "/extract", response_model=EntityExtractionResponse,
    summary="Extract entities (suggestion)",
)
async def extract(
    service: EntityExtractionServiceDep, data: TextRequest
) -> EntityExtractionResponse:
    result = await service.extract(
        data.text, language=data.language, provider=data.provider,
        call_id=data.call_id, incident_id=data.incident_id,
    )
    return extraction_to_response(result)


@router.post(
    "/classify", response_model=ClassificationResponse,
    summary="Classify incident (recommendation)",
)
async def classify(
    service: ClassificationServiceDep, data: TextRequest
) -> ClassificationResponse:
    result = await service.classify(
        data.text, language=data.language, provider=data.provider,
        call_id=data.call_id, incident_id=data.incident_id,
    )
    return classification_to_response(result)


@router.post(
    "/summarize", response_model=SummaryResponse, summary="Summarize the call"
)
async def summarize(
    service: SummaryServiceDep, data: TextRequest
) -> SummaryResponse:
    result = await service.summarize(
        data.text, language=data.language, provider=data.provider,
        call_id=data.call_id, incident_id=data.incident_id,
    )
    return summary_to_response(result)


@router.post(
    "/analyze", response_model=AnalysisResponse,
    summary="Combined analysis (summary + entities + classification)",
)
async def analyze(
    service: AnalysisServiceDep, data: TextRequest
) -> AnalysisResponse:
    result = await service.analyze(
        data.text, language=data.language, provider=data.provider,
        call_id=data.call_id, incident_id=data.incident_id,
    )
    return analysis_to_response(result)


@router.post(
    "/calls/{call_id}/analyze", response_model=AnalysisResponse,
    summary="Analyze a call's transcript (Call Management integration)",
)
async def analyze_call(
    pipeline: CallAnalysisPipelineDep, call_id: UUID, data: CallAnalysisRequest
) -> AnalysisResponse:
    result = await pipeline.analyze_call(call_id, provider=data.provider)
    return analysis_to_response(result)


@router.get(
    "/providers", response_model=AIProvidersResponse, summary="List AI providers"
)
async def list_providers(registry: AIRegistryDep) -> AIProvidersResponse:
    infos = []
    for provider in registry.all():
        health = await provider.health_check()
        infos.append(
            provider_info(
                provider, health=health,
                is_default=provider.name == registry.default_name,
            )
        )
    return AIProvidersResponse(default=registry.default_name, providers=infos)


@router.get("/health", response_model=AIHealthResponse, summary="AI platform health")
async def health(registry: AIRegistryDep) -> AIHealthResponse:
    infos = []
    healthy = True
    for provider in registry.all():
        h = await provider.health_check()
        healthy = healthy and h.healthy
        infos.append(
            provider_info(
                provider, health=h,
                is_default=provider.name == registry.default_name,
            )
        )
    return AIHealthResponse(healthy=healthy and bool(infos), providers=infos)


@router.get(
    "/audit", response_model=list[AIAuditResponse], summary="AI audit log"
)
async def audit(
    repo: AIAuditRepoDep,
    capability: AIAuditCapability | None = Query(default=None),
    provider: str | None = Query(default=None),
    call_id: UUID | None = Query(default=None),
    incident_id: UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[AIAuditResponse]:
    rows = await repo.list_entries(
        capability=capability, provider=provider, call_id=call_id,
        incident_id=incident_id, limit=limit, offset=offset,
    )
    return [audit_to_response(r) for r in rows]
