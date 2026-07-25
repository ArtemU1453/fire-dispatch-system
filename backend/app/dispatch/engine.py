"""DispatchEngine — coordinates the recommendation pipeline.

Implements the twelve-step flow for one incident:

1-2. get incident parameters and the **active rules** from the Rule Engine;
3.   determine required capabilities (consolidated requirements);
4.   fetch candidates near the incident via the Search Engine;
5-7. exclude unavailable resources, check capabilities, check service zones —
     every exclusion is captured with a reason;
8-10. determine the minimum composition, pick the recommended composition and
     the reserve;
11.  build the explanation for every choice;
12.  return the recommendation (advisory — nothing is dispatched).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from uuid import UUID

from app.dispatch.algorithms.candidate import DispatchCandidate
from app.dispatch.algorithms.capability_analyzer import CapabilityAnalyzer
from app.dispatch.algorithms.coverage_validator import CoverageValidator
from app.dispatch.algorithms.priority_resolver import PriorityResolver
from app.dispatch.algorithms.reserve_selector import ReserveSelector
from app.dispatch.algorithms.resource_selector import ResourceSelector
from app.dispatch.algorithms.scoring import Scorer
from app.dispatch.config import DispatchConfig
from app.dispatch.eta import ETAProvider
from app.dispatch.models.enums import ExclusionReason, RecommendationRole
from app.dispatch.recommendations.builder import RecommendationBuilder
from app.dispatch.recommendations.models import ExcludedResource, Recommendation
from app.dispatch.repositories import CandidateRepository
from app.dispatch.requirements import RequirementAggregator, RequirementSet
from app.rules.engine import RuleEngine
from app.rules.executors import EvaluationContext
from app.search.criteria import GeoPoint


@dataclass(slots=True)
class IncidentContext:
    """Resolved facts about the incident the engine reasons over."""

    incident_type_id: UUID
    latitude: float
    longitude: float
    complexity: str | None = None
    time_of_day_hour: int | None = None
    administrative_area_id: UUID | None = None
    object_type: str | None = None
    danger_level: str | None = None
    flags: list[str] = field(default_factory=list)
    # Manual dispatcher constraints.
    organization_ids: list[UUID] = field(default_factory=list)
    excluded_resource_ids: set[UUID] = field(default_factory=set)
    radius_override_meters: float | None = None


@dataclass(slots=True)
class DispatchOutcome:
    """The engine's full result: the recommendation plus the evaluation log."""

    recommendation: Recommendation
    requirements: RequirementSet
    eligible: list[DispatchCandidate]
    selected_ids: set[UUID]
    reserve_ids: set[UUID]


class DispatchEngine:
    """Coordinates rules, candidates, exclusion, selection and recommendation."""

    def __init__(
        self,
        rule_engine: RuleEngine,
        candidate_repository: CandidateRepository,
        *,
        config: DispatchConfig | None = None,
        eta_provider: ETAProvider | None = None,
        resource_selector: ResourceSelector | None = None,
    ) -> None:
        self._rules = rule_engine
        self._candidates = candidate_repository
        self._config = config or DispatchConfig()
        self._eta = eta_provider
        self._aggregator = RequirementAggregator(self._config)
        self._analyzer = CapabilityAnalyzer()
        self._priority = PriorityResolver()
        self._selector = resource_selector or ResourceSelector()
        self._reserve = ReserveSelector()
        self._validator = CoverageValidator()
        self._builder = RecommendationBuilder(self._config)

    async def recommend(
        self, incident: IncidentContext, *, preview: bool = False
    ) -> DispatchOutcome:
        # 2. active rules from the Rule Engine, 3. consolidated requirements.
        applicable = await self._rules.find_applicable(self._context(incident))
        requirements = self._aggregator.aggregate(applicable)
        radius = incident.radius_override_meters or requirements.search_radius_meters

        # 4. candidates near the incident.
        raw = await self._candidates.fetch_candidates(
            GeoPoint(incident.latitude, incident.longitude),
            categories=requirements.resource_categories,
            radius_meters=radius,
            limit=self._config.candidate_limit,
            organization_ids=incident.organization_ids,
        )

        # 5-7. exclude unavailable / missing capability / out-of-zone.
        eligible, excluded = self._partition(raw, requirements, incident)

        # 8-10. score, rank, select primary + reserve.
        self._score(eligible, requirements)
        ranked = self._priority.rank_candidates(eligible)
        primary = self._selector.select_primary(requirements, ranked)
        primary_ids = {c.id for c in primary}
        reserve = (
            []
            if preview
            else self._reserve.select_reserve(requirements, ranked, primary_ids)
        )
        reserve_ids = {c.id for c in reserve}

        # 11. coverage, sufficiency and explanation.
        labels = await self._candidates.resolve_capability_labels(
            requirements.required_capability_codes
        )
        priority = self._priority.resolve(requirements, incident.danger_level)
        coverage = self._analyzer.coverage(requirements, primary, labels)
        sufficient, messages = self._validator.validate(
            requirements, len(primary), coverage
        )

        recommendation = self._builder.build(
            requirements=requirements,
            incident_type_id=incident.incident_type_id,
            latitude=incident.latitude,
            longitude=incident.longitude,
            priority=priority,
            primary=primary,
            reserve=reserve,
            excluded=excluded,
            coverage=coverage,
            sufficient=sufficient,
            messages=messages,
            total_candidates=len(raw),
            is_preview=preview,
        )
        return DispatchOutcome(
            recommendation=recommendation,
            requirements=requirements,
            eligible=ranked,
            selected_ids=primary_ids,
            reserve_ids=reserve_ids,
        )

    # ---------------------------------------------------------- internals
    def _context(self, incident: IncidentContext) -> EvaluationContext:
        return EvaluationContext(
            incident_type_id=incident.incident_type_id,
            complexity=incident.complexity,
            time_of_day_hour=incident.time_of_day_hour,
            administrative_area_id=incident.administrative_area_id,
            object_type=incident.object_type,
        )

    def _partition(
        self,
        candidates: Sequence[DispatchCandidate],
        requirements: RequirementSet,
        incident: IncidentContext,
    ) -> tuple[list[DispatchCandidate], list[ExcludedResource]]:
        eligible: list[DispatchCandidate] = []
        excluded: list[ExcludedResource] = []
        for candidate in candidates:
            reason = self._exclusion_reason(candidate, requirements, incident)
            if reason is None:
                eligible.append(candidate)
            else:
                excluded.append(
                    ExcludedResource(
                        candidate=candidate, reason=reason[0], detail=reason[1]
                    )
                )
        return eligible, excluded

    def _exclusion_reason(
        self,
        candidate: DispatchCandidate,
        requirements: RequirementSet,
        incident: IncidentContext,
    ) -> tuple[ExclusionReason, str | None] | None:
        # Manual dispatcher exclusion.
        if candidate.id in incident.excluded_resource_ids:
            return ExclusionReason.MANUAL_EXCLUSION, "Исключено диспетчером."

        # Availability.
        status = candidate.resource.availability_status
        policy = self._config.exclusions
        if status is None:
            return ExclusionReason.NOT_OPERATIONAL, "Нет статуса готовности."
        if status.code in policy.excluded_status_codes:
            return ExclusionReason.UNAVAILABLE_STATUS, f"Статус: {status.code}."
        if policy.require_operational and not status.is_operational:
            return ExclusionReason.NOT_OPERATIONAL, "Не в строю."
        if policy.require_deployable and not status.is_available_for_dispatch:
            return ExclusionReason.NOT_DEPLOYABLE, "Недоступно для направления."

        # Capability.
        if not self._analyzer.provides_any_required(candidate, requirements):
            return ExclusionReason.MISSING_CAPABILITY, "Нет требуемых возможностей."

        # Service zone (by administrative area; geometry routing is a later stage).
        if (
            incident.administrative_area_id is not None
            and candidate.service_area_ids
            and incident.administrative_area_id not in candidate.service_area_ids
        ):
            return ExclusionReason.OUT_OF_SERVICE_ZONE, "Вне зоны обслуживания."

        return None

    def _score(
        self, candidates: Sequence[DispatchCandidate], requirements: RequirementSet
    ) -> None:
        scorer = Scorer(
            self._config,
            requirements.required_capability_codes,
            eta_provider=self._eta,
        )
        for candidate in candidates:
            candidate.score = scorer.score(
                distance_meters=candidate.distance_meters,
                readiness=candidate.readiness,
                capabilities=candidate.capabilities,
            )


__all__ = [
    "DispatchEngine",
    "DispatchOutcome",
    "IncidentContext",
    "RecommendationRole",
]
