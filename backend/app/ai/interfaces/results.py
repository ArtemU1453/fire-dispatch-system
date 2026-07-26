"""Result envelopes returned by an :class:`AIProvider`.

These are plain dataclasses (not Pydantic and not ORM), so providers stay pure
and free of persistence / transport concerns. Every result carries an
:class:`AIResultMeta` describing **which model produced it, its version, the
confidence and the processing time** — the audit / recommendation metadata the
platform needs (stage §8).

Nothing here mutates any domain entity: results are **suggestions** for the
dispatcher only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AICapability(str, Enum):
    """The intelligent capabilities exposed by the platform."""

    TRANSCRIBE = "transcribe"
    EXTRACT_ENTITIES = "extract_entities"
    CLASSIFY_INCIDENT = "classify_incident"
    SUMMARIZE = "summarize"
    ANALYZE = "analyze"


@dataclass(slots=True)
class AIResultMeta:
    """Provenance for a single AI result (stage §8)."""

    provider: str
    model: str
    model_version: str
    confidence: float
    processing_ms: int


@dataclass(slots=True)
class TranscriptSegment:
    start_ms: int
    end_ms: int
    text: str
    confidence: float


@dataclass(slots=True)
class TranscriptionResult:
    text: str
    language: str
    confidence: float
    segments: list[TranscriptSegment] = field(default_factory=list)
    meta: AIResultMeta | None = None


@dataclass(slots=True)
class ExtractedEntities:
    """The structured entities suggested from a conversation (stage §5)."""

    address: str | None = None
    incident_type: str | None = None
    category: str | None = None
    objects: list[str] = field(default_factory=list)
    phone: str | None = None
    reporter_name: str | None = None
    extra: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class EntityExtractionResult:
    entities: ExtractedEntities
    meta: AIResultMeta | None = None


@dataclass(slots=True)
class ClassificationResult:
    """A suggested classification (stage §6) — never applied automatically."""

    incident_type_code: str | None
    incident_type_name: str | None
    category: str
    priority: str
    meta: AIResultMeta | None = None


@dataclass(slots=True)
class SummaryResult:
    summary: str
    meta: AIResultMeta | None = None


@dataclass(slots=True)
class AnalysisResult:
    """A combined analysis: summary + entities + classification (stage §7/§9)."""

    summary: str
    entities: ExtractedEntities
    classification: ClassificationResult
    meta: AIResultMeta | None = None


@dataclass(slots=True)
class ProviderHealth:
    healthy: bool
    provider: str
    models: list[str] = field(default_factory=list)
    capabilities: list[AICapability] = field(default_factory=list)
    detail: str | None = None
