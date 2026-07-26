"""AI platform interfaces and result types (the abstraction layer)."""

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

__all__ = [
    "AICapability",
    "AIProvider",
    "AIResultMeta",
    "AnalysisResult",
    "ClassificationResult",
    "EntityExtractionResult",
    "ExtractedEntities",
    "ProviderHealth",
    "SummaryResult",
    "TranscriptSegment",
    "TranscriptionResult",
]
