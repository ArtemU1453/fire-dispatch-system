"""Recommendation scoring.

Each candidate gets a 0..1 :class:`RecommendationScore` combining sub-scores —
distance, readiness, capability match, and (future) arrival time. Weights come
from :class:`DispatchConfig` and are renormalized over the *active* components,
so the ``arrival_time`` weight penalises no one until an :class:`ETAProvider`
returns a value (the routing stage).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from app.dispatch.config import DispatchConfig
from app.dispatch.eta import ETAProvider, NullETAProvider

# Readiness states, ordered best-first.
READY_DEPLOYABLE = "deployable"
READY_OPERATIONAL = "operational"
READY_OTHER = "other"


@dataclass(slots=True)
class RecommendationScore:
    """A candidate's total score plus a transparent per-component breakdown."""

    total: float
    breakdown: dict[str, float] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)


class Scorer:
    """Turns candidate attributes into a :class:`RecommendationScore`."""

    def __init__(
        self,
        config: DispatchConfig,
        required_capabilities: Sequence[str] = (),
        *,
        eta_provider: ETAProvider | None = None,
    ) -> None:
        self._config = config
        self._required = list(required_capabilities)
        self._eta = eta_provider or NullETAProvider()

    def score(
        self,
        *,
        distance_meters: float | None,
        readiness: str,
        capabilities: dict[str, int],
    ) -> RecommendationScore:
        weights = self._config.weights
        components: dict[str, float] = {}
        active_weights: dict[str, float] = {}
        reasons: list[str] = []

        components["distance"] = self._distance_score(distance_meters)
        active_weights["distance"] = weights.distance
        if distance_meters is not None:
            reasons.append(f"расстояние {round(distance_meters)} м")

        components["readiness"] = self._readiness_score(readiness)
        active_weights["readiness"] = weights.readiness
        reasons.append(f"готовность: {readiness}")

        cap_score, matched = self._capability_score(capabilities)
        components["capability_match"] = cap_score
        active_weights["capability_match"] = weights.capability_match
        if self._required:
            reasons.append(
                "обеспечивает: " + (", ".join(matched) if matched else "—")
            )

        arrival = self._eta.estimate(distance_meters)
        if arrival is not None:
            components["arrival_time"] = self._arrival_score(arrival)
            active_weights["arrival_time"] = weights.arrival_time
            reasons.append(f"прибытие ~{round(arrival)} с")

        total = self._weighted(components, active_weights)
        return RecommendationScore(total=total, breakdown=components, reasons=reasons)

    # ------------------------------------------------------------ helpers
    def _distance_score(self, distance_meters: float | None) -> float:
        if distance_meters is None:
            return 0.0
        max_d = self._config.max_distance_meters
        return max(0.0, min(1.0, 1.0 - distance_meters / max_d))

    def _readiness_score(self, readiness: str) -> float:
        scores = self._config.readiness_scores
        return {
            READY_DEPLOYABLE: scores.deployable,
            READY_OPERATIONAL: scores.operational,
            READY_OTHER: scores.other,
        }.get(readiness, scores.other)

    def _capability_score(
        self, capabilities: dict[str, int]
    ) -> tuple[float, list[str]]:
        if not self._required:
            return 1.0, []
        matched = [c for c in self._required if capabilities.get(c, 0) > 0]
        return len(matched) / len(self._required), matched

    def _arrival_score(self, arrival_seconds: float) -> float:
        # Placeholder normalisation for when a provider is present; the real curve
        # arrives with the routing stage. Bounded to 0..1.
        return max(0.0, min(1.0, 1.0 - arrival_seconds / 1800.0))

    @staticmethod
    def _weighted(
        components: dict[str, float], weights: dict[str, float]
    ) -> float:
        total_weight = sum(weights.values())
        if total_weight <= 0:
            return 0.0
        return sum(components[k] * weights[k] for k in weights) / total_weight
