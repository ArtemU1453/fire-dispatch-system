"""Domain objects for a dispatch recommendation (not API schemas, not ORM)."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.dispatch.algorithms.candidate import DispatchCandidate
from app.dispatch.models.enums import (
    ConfidenceLevel,
    DispatchStatus,
    ExclusionReason,
    RecommendationRole,
)
from app.rules.models.enums import RulePriority


@dataclass(slots=True)
class CapabilityCoverage:
    """How a required capability is covered by the selected units."""

    code: str
    label: str | None
    required: int
    provided: int
    mandatory: bool = True

    @property
    def satisfied(self) -> bool:
        return self.provided >= self.required


@dataclass(slots=True)
class RecommendedUnit:
    """A selected candidate with its role and rationale."""

    candidate: DispatchCandidate
    role: RecommendationRole
    reasons: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ExcludedResource:
    """A considered resource that was excluded, with the reason (for the log)."""

    candidate: DispatchCandidate
    reason: ExclusionReason
    detail: str | None = None


@dataclass(slots=True)
class Recommendation:
    """The recommendation returned to the dispatcher (advisory only)."""

    incident_type_id: object
    latitude: float
    longitude: float
    priority: RulePriority
    status: DispatchStatus
    primary_units: list[RecommendedUnit] = field(default_factory=list)
    reserve_units: list[RecommendedUnit] = field(default_factory=list)
    capability_coverage: list[CapabilityCoverage] = field(default_factory=list)
    excluded: list[ExcludedResource] = field(default_factory=list)
    sufficient: bool = False
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    confidence_score: float = 0.0
    total_candidates: int = 0
    minimum_units: int = 0
    recommended_units: int = 0
    reserve_units_target: int = 0
    messages: list[str] = field(default_factory=list)
    global_reasons: list[str] = field(default_factory=list)
    rule_ids: list[object] = field(default_factory=list)
    rule_codes: list[str] = field(default_factory=list)
    is_preview: bool = False
