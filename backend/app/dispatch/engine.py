"""DispatchEngine — coordinates the recommendation pipeline.

Orchestrates the components for one incident: look up the rule, fetch available
candidates near the incident (Stage-4 search), score them (configurable),
rank them, and hand off to the RecommendationEngine to assemble the advisory
recommendation. It never sends units anywhere.

Decision flow:
    rule → candidates → filter/exclude → score → rank → compose → recommend
"""

from __future__ import annotations

from app.dispatch.algorithms.candidate import DispatchCandidate
from app.dispatch.algorithms.scoring import ArrivalEstimator, Scorer
from app.dispatch.recommendations import Recommendation, RecommendationEngine
from app.dispatch.repositories import CandidateRepository
from app.dispatch.rules import RuleEngine
from app.search.criteria import GeoPoint


class DispatchEngine:
    """Coordinates rule lookup, candidate search, scoring and recommendation."""

    def __init__(
        self,
        candidate_repository: CandidateRepository,
        rule_engine: RuleEngine,
        *,
        arrival_estimator: ArrivalEstimator | None = None,
    ) -> None:
        self._candidates = candidate_repository
        self._rules = rule_engine
        self._recommender = RecommendationEngine(rule_engine.scoring)
        self._arrival = arrival_estimator

    async def recommend(
        self,
        *,
        incident_type: str,
        latitude: float,
        longitude: float,
        preview: bool = False,
    ) -> Recommendation:
        rule = self._rules.incident_rule(incident_type)
        point = GeoPoint(latitude, longitude)

        candidates = await self._candidates.fetch_candidates(
            point, rule, self._rules.exclusions
        )
        self._score(candidates, rule)
        candidates.sort(key=lambda c: c.score_value, reverse=True)

        return self._recommender.build(
            rule=rule,
            latitude=latitude,
            longitude=longitude,
            candidates=candidates,
            preview=preview,
        )

    def _score(
        self, candidates: list[DispatchCandidate], rule
    ) -> None:
        scorer = Scorer(
            self._rules.scoring,
            [c.code for c in rule.required_capabilities],
            arrival_estimator=self._arrival,
        )
        for candidate in candidates:
            candidate.score = scorer.score(
                distance_meters=candidate.distance_meters,
                readiness=candidate.readiness,
                capabilities=candidate.capabilities,
            )
