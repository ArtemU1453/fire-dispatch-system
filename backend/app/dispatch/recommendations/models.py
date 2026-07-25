"""Domain objects for a dispatch recommendation (not API schemas)."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.dispatch.algorithms.candidate import DispatchCandidate

# Roles a recommended unit can play.
ROLE_PRIMARY = "primary"
ROLE_RESERVE = "reserve"

# Confidence labels.
CONFIDENCE_HIGH = "high"
CONFIDENCE_MEDIUM = "medium"
CONFIDENCE_LOW = "low"


@dataclass(slots=True)
class CapabilityCoverage:
    """How a required capability is covered by the selected units."""

    code: str
    label: str | None
    required: int
    provided: int

    @property
    def satisfied(self) -> bool:
        return self.provided >= self.required


@dataclass(slots=True)
class RecommendedUnit:
    """A selected candidate with its role and rationale."""

    candidate: DispatchCandidate
    role: str
    reasons: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Recommendation:
    """The recommendation returned to the dispatcher (advisory only)."""

    incident_type: str
    incident_name: str
    priority: int
    latitude: float
    longitude: float
    primary_units: list[RecommendedUnit] = field(default_factory=list)
    reserve_units: list[RecommendedUnit] = field(default_factory=list)
    capability_coverage: list[CapabilityCoverage] = field(default_factory=list)
    sufficient: bool = False
    confidence: str = CONFIDENCE_LOW
    confidence_score: float = 0.0
    total_candidates: int = 0
    messages: list[str] = field(default_factory=list)
    is_preview: bool = False
