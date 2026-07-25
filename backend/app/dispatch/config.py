"""Dispatch engine configuration (policy, not norms).

The **norms** (which capabilities / how many units an incident needs) come from
the database Rule Engine. What remains here is engine *policy*: how to rank
eligible candidates and which availability states count as excluded. Everything
has a sensible default and can be overridden by constructing a custom
:class:`DispatchConfig` — no coefficient is hard-wired into the algorithms.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ScoringWeights:
    """Relative weights of the scoring components (renormalized over active)."""

    distance: float = 0.4
    readiness: float = 0.3
    capability_match: float = 0.3
    arrival_time: float = 0.0  # activated only when an ETA provider is present


@dataclass(frozen=True, slots=True)
class ReadinessScores:
    """Sub-scores for readiness states (0..1)."""

    deployable: float = 1.0
    operational: float = 0.5
    other: float = 0.1


@dataclass(frozen=True, slots=True)
class ConfidenceThresholds:
    high: float = 0.75
    medium: float = 0.5


@dataclass(frozen=True, slots=True)
class ExclusionPolicy:
    """Which resources are excluded before selection."""

    require_operational: bool = True
    require_deployable: bool = True
    excluded_status_codes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DispatchConfig:
    """Top-level engine configuration."""

    weights: ScoringWeights = field(default_factory=ScoringWeights)
    readiness_scores: ReadinessScores = field(default_factory=ReadinessScores)
    confidence: ConfidenceThresholds = field(default_factory=ConfidenceThresholds)
    exclusions: ExclusionPolicy = field(default_factory=ExclusionPolicy)
    # Spatial search defaults (rules describe composition, not geography).
    default_search_radius_meters: float = 15000.0
    candidate_limit: int = 100
    max_distance_meters: float = 30000.0
