"""AI-platform application services (one per capability + combined analysis)."""

from __future__ import annotations

from app.ai.services.analysis_service import AnalysisService
from app.ai.services.audit import AIAuditRecorder
from app.ai.services.base import AIServiceBase
from app.ai.services.classification_service import ClassificationService
from app.ai.services.entity_extraction_service import EntityExtractionService
from app.ai.services.summary_service import SummaryService
from app.ai.services.transcription_service import TranscriptionService

__all__ = [
    "AIAuditRecorder",
    "AIServiceBase",
    "AnalysisService",
    "ClassificationService",
    "EntityExtractionService",
    "SummaryService",
    "TranscriptionService",
]
