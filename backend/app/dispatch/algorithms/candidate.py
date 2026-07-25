"""The dispatch candidate — a resource enriched for recommendation.

Wraps a resource with the attributes the recommendation logic needs: distance to
the incident, readiness state, the capabilities it provides (code → quantity) and
its computed score. Keeps ORM access explicit so mapping to schemas is trivial.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from app.dispatch.algorithms.scoring import RecommendationScore
from app.models.resource import Resource


@dataclass(slots=True)
class DispatchCandidate:
    resource: Resource
    distance_meters: float | None
    readiness: str
    capabilities: dict[str, int] = field(default_factory=dict)
    score: RecommendationScore | None = None

    @property
    def id(self) -> UUID:
        return self.resource.id

    @property
    def score_value(self) -> float:
        return self.score.total if self.score is not None else 0.0
