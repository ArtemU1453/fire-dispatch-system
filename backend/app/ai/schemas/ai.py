"""Pydantic schemas for the AI platform (stage §11).

Every result schema carries an :class:`AIResultMeta` (provider / model / version /
confidence / processing time) and is flagged ``advisory=True`` — the platform's
output is always a **recommendation** for the dispatcher, never an applied action.
"""

from __future__ import annotations

from uuid import UUID

from app.ai.models.enums import AIAuditCapability, AIAuditStatus
from app.schemas.common import ResponseBase, SchemaBase


# ------------------------------------------------------------------ meta ---
class AIResultMeta(SchemaBase):
    provider: str
    model: str
    model_version: str
    confidence: float
    processing_ms: int


# --------------------------------------------------------------- requests ---
class TranscriptionRequest(SchemaBase):
    audio_ref: str | None = None
    language: str | None = "ru"
    # Offline / mock providers may be fed known text instead of audio.
    sample_text: str | None = None
    provider: str | None = None
    call_id: UUID | None = None


class TextRequest(SchemaBase):
    """Common input for extraction / classification / summary / analysis."""

    text: str
    language: str = "ru"
    provider: str | None = None
    call_id: UUID | None = None
    incident_id: UUID | None = None


class CallAnalysisRequest(SchemaBase):
    provider: str | None = None


# -------------------------------------------------------------- responses ---
class TranscriptSegmentSchema(SchemaBase):
    start_ms: int
    end_ms: int
    text: str
    confidence: float


class TranscriptionResponse(SchemaBase):
    text: str
    language: str
    confidence: float
    segments: list[TranscriptSegmentSchema] = []
    meta: AIResultMeta | None = None


class ExtractedEntitiesSchema(SchemaBase):
    address: str | None = None
    incident_type: str | None = None
    category: str | None = None
    objects: list[str] = []
    phone: str | None = None
    reporter_name: str | None = None
    extra: dict[str, str] = {}


class EntityExtractionResponse(SchemaBase):
    entities: ExtractedEntitiesSchema
    meta: AIResultMeta | None = None
    advisory: bool = True


class ClassificationResponse(SchemaBase):
    incident_type_code: str | None = None
    incident_type_name: str | None = None
    category: str
    priority: str
    meta: AIResultMeta | None = None
    advisory: bool = True


class SummaryResponse(SchemaBase):
    summary: str
    meta: AIResultMeta | None = None
    advisory: bool = True


class AnalysisResponse(SchemaBase):
    summary: str
    entities: ExtractedEntitiesSchema
    classification: ClassificationResponse
    meta: AIResultMeta | None = None
    advisory: bool = True


# ------------------------------------------------------- providers / health ---
class AIProviderInfo(SchemaBase):
    name: str
    model: str
    model_version: str
    capabilities: list[str] = []
    healthy: bool
    is_default: bool = False


class AIProvidersResponse(SchemaBase):
    default: str | None = None
    providers: list[AIProviderInfo] = []


class AIHealthResponse(SchemaBase):
    healthy: bool
    providers: list[AIProviderInfo] = []


# ----------------------------------------------------------------- audit ---
class AIAuditResponse(ResponseBase):
    capability: AIAuditCapability
    status: AIAuditStatus
    provider: str
    model: str
    model_version: str
    confidence: float | None = None
    processing_ms: int | None = None
    latency_ms: int | None = None
    language: str | None = None
    error: str | None = None
    call_id: UUID | None = None
    incident_id: UUID | None = None
