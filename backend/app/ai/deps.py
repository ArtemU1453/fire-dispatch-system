"""AI-platform dependency providers (Dependency Injection wiring).

The provider **registry** is a process-wide singleton, so several providers can
be registered once and selected per request. Services and the pipeline are built
from the request's DB session plus that shared registry — swapping or adding a
provider never touches the endpoints.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.ai.pipelines import CallAnalysisPipeline
from app.ai.providers.registry import AIProviderRegistry, default_registry
from app.ai.repositories import AIAuditRepository
from app.ai.services import (
    AnalysisService,
    ClassificationService,
    EntityExtractionService,
    SummaryService,
    TranscriptionService,
)
from app.api.deps import SessionDep

# One shared registry for the whole process (pre-loaded with the mock provider).
_registry: AIProviderRegistry = default_registry()


def get_ai_registry() -> AIProviderRegistry:
    return _registry


AIRegistryDep = Annotated[AIProviderRegistry, Depends(get_ai_registry)]


def get_transcription_service(
    session: SessionDep, registry: AIRegistryDep
) -> TranscriptionService:
    return TranscriptionService(session, registry=registry)


def get_entity_extraction_service(
    session: SessionDep, registry: AIRegistryDep
) -> EntityExtractionService:
    return EntityExtractionService(session, registry=registry)


def get_classification_service(
    session: SessionDep, registry: AIRegistryDep
) -> ClassificationService:
    return ClassificationService(session, registry=registry)


def get_summary_service(
    session: SessionDep, registry: AIRegistryDep
) -> SummaryService:
    return SummaryService(session, registry=registry)


def get_analysis_service(
    session: SessionDep, registry: AIRegistryDep
) -> AnalysisService:
    return AnalysisService(session, registry=registry)


def get_call_analysis_pipeline(
    session: SessionDep, registry: AIRegistryDep
) -> CallAnalysisPipeline:
    return CallAnalysisPipeline(session, registry=registry)


def get_ai_audit_repo(session: SessionDep) -> AIAuditRepository:
    return AIAuditRepository(session)


TranscriptionServiceDep = Annotated[
    TranscriptionService, Depends(get_transcription_service)
]
EntityExtractionServiceDep = Annotated[
    EntityExtractionService, Depends(get_entity_extraction_service)
]
ClassificationServiceDep = Annotated[
    ClassificationService, Depends(get_classification_service)
]
SummaryServiceDep = Annotated[SummaryService, Depends(get_summary_service)]
AnalysisServiceDep = Annotated[AnalysisService, Depends(get_analysis_service)]
CallAnalysisPipelineDep = Annotated[
    CallAnalysisPipeline, Depends(get_call_analysis_pipeline)
]
AIAuditRepoDep = Annotated[AIAuditRepository, Depends(get_ai_audit_repo)]
