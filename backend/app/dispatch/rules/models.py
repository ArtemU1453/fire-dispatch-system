"""Rule model definitions (validated with Pydantic v2).

These mirror the externalized rules file so the whole rule set is validated on
load. Rules live **outside** the code (a YAML file, see ``default_rules.yaml``)
and are looked up by incident-type code, so operators add/adjust rules and tune
every coefficient without touching Python — no magic values in the algorithm.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ResourceCategory


class RuleBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CapabilityRequirement(RuleBase):
    """A capability an incident needs, with the minimum quantity required."""

    code: str
    min_quantity: int = Field(default=1, ge=1)
    label: str | None = None


class ReadinessScores(RuleBase):
    """Readiness sub-score by availability state (0..1)."""

    deployable: float = 1.0
    operational: float = 0.5
    other: float = 0.0


class ScoringWeights(RuleBase):
    """Relative weights of the score components (need not sum to 1)."""

    distance: float = 0.5
    readiness: float = 0.2
    capability_match: float = 0.2
    arrival_time: float = 0.1


class ConfidenceConfig(RuleBase):
    """Thresholds turning a coverage/availability ratio into a label."""

    high_threshold: float = 0.85
    medium_threshold: float = 0.5


class ScoringConfig(RuleBase):
    """All tunable scoring parameters (no coefficient is hard-coded)."""

    weights: ScoringWeights = Field(default_factory=ScoringWeights)
    readiness_scores: ReadinessScores = Field(default_factory=ReadinessScores)
    # Distance beyond which the distance sub-score is 0 (linear decay to it).
    max_distance_meters: float = 50_000.0
    confidence: ConfidenceConfig = Field(default_factory=ConfidenceConfig)


class ExclusionConfig(RuleBase):
    """Which resources are excluded from consideration."""

    require_active: bool = True
    require_operational: bool = True
    require_deployable: bool = True
    # Availability-status codes explicitly excluded (e.g. maintenance, busy).
    excluded_status_codes: list[str] = Field(default_factory=list)


class IncidentRule(RuleBase):
    """The dispatch rule for one incident type."""

    code: str
    name: str
    priority: int = Field(default=3, ge=1, description="1 = highest priority.")
    resource_categories: list[ResourceCategory] = Field(default_factory=list)
    required_capabilities: list[CapabilityRequirement] = Field(default_factory=list)
    minimum_units: int = Field(default=1, ge=0)
    recommended_units: int = Field(default=1, ge=0)
    reserve_units: int = Field(default=0, ge=0)
    search_radius_meters: float = Field(default=50_000.0, gt=0)
    candidate_limit: int = Field(default=100, ge=1, le=1000)


class DispatchRules(RuleBase):
    """The complete rule set loaded from configuration."""

    version: str = "1"
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    exclusions: ExclusionConfig = Field(default_factory=ExclusionConfig)
    incident_types: dict[str, IncidentRule] = Field(default_factory=dict)
