"""RecommendationBuilder — assembles the advisory recommendation.

Given the selected primary and reserve units, the excluded resources (with
reasons), the capability coverage and the sufficiency verdict, it produces the
domain :class:`Recommendation`: it labels confidence, generates an automatic
explanation for every selected unit and for the decision as a whole, and sets the
outcome status. It dispatches nothing.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from app.dispatch.algorithms.candidate import DispatchCandidate
from app.dispatch.config import DispatchConfig
from app.dispatch.models.enums import (
    ConfidenceLevel,
    DispatchStatus,
    RecommendationRole,
)
from app.dispatch.recommendations.models import (
    CapabilityCoverage,
    ExcludedResource,
    Recommendation,
    RecommendedUnit,
)
from app.dispatch.requirements import RequirementSet
from app.rules.models.enums import RulePriority


class RecommendationBuilder:
    """Builds a :class:`Recommendation` from the selection outcome."""

    def __init__(self, config: DispatchConfig | None = None) -> None:
        self._config = config or DispatchConfig()

    def build(
        self,
        *,
        requirements: RequirementSet,
        incident_type_id: UUID,
        latitude: float,
        longitude: float,
        priority: RulePriority,
        primary: Sequence[DispatchCandidate],
        reserve: Sequence[DispatchCandidate],
        excluded: Sequence[ExcludedResource],
        coverage: Sequence[CapabilityCoverage],
        sufficient: bool,
        messages: Sequence[str],
        total_candidates: int,
        is_preview: bool = False,
    ) -> Recommendation:
        confidence_score = self._confidence_score(requirements, primary, coverage)
        confidence = self._confidence_label(confidence_score)
        status = self._status(sufficient, len(primary), total_candidates)

        return Recommendation(
            incident_type_id=incident_type_id,
            latitude=latitude,
            longitude=longitude,
            priority=priority,
            status=status,
            primary_units=[
                self._unit(c, RecommendationRole.PRIMARY, requirements)
                for c in primary
            ],
            reserve_units=[
                self._unit(c, RecommendationRole.RESERVE, requirements)
                for c in reserve
            ],
            capability_coverage=list(coverage),
            excluded=list(excluded),
            sufficient=sufficient,
            confidence=confidence,
            confidence_score=round(confidence_score, 4),
            total_candidates=total_candidates,
            minimum_units=requirements.minimum_units,
            recommended_units=requirements.recommended_units,
            reserve_units_target=requirements.reserve_units,
            messages=list(messages),
            global_reasons=self._global_reasons(coverage, sufficient),
            rule_ids=list(requirements.rule_ids),
            rule_codes=list(requirements.rule_codes),
            is_preview=is_preview,
        )

    # -------------------------------------------------------- explanation
    def _unit(
        self,
        candidate: DispatchCandidate,
        role: RecommendationRole,
        requirements: RequirementSet,
    ) -> RecommendedUnit:
        reasons: list[str] = []
        matched = [
            code
            for code in requirements.capabilities
            if candidate.provides(code)
        ]
        clauses = ["доступно"]
        if matched:
            clauses.append("имеет требуемые возможности (" + ", ".join(matched) + ")")
        if candidate.distance_meters is not None:
            clauses.append(f"на удалении {round(candidate.distance_meters)} м")
        clauses.append("соответствует действующим правилам")
        verb = "Основной" if role is RecommendationRole.PRIMARY else "Резерв"
        reasons.append(f"{verb}: подразделение " + ", ".join(clauses) + ".")
        if candidate.score is not None:
            reasons.extend(candidate.score.reasons)
        return RecommendedUnit(candidate=candidate, role=role, reasons=reasons)

    @staticmethod
    def _global_reasons(
        coverage: Sequence[CapabilityCoverage], sufficient: bool
    ) -> list[str]:
        reasons: list[str] = []
        covered = [c.code for c in coverage if c.satisfied]
        missing = [c.code for c in coverage if not c.satisfied]
        if covered:
            reasons.append("Покрыты возможности: " + ", ".join(sorted(covered)) + ".")
        if missing:
            reasons.append("Не покрыты: " + ", ".join(sorted(missing)) + ".")
        reasons.append(
            "Состав достаточен." if sufficient else "Состав неполный."
        )
        return reasons

    # -------------------------------------------------------- confidence
    def _confidence_score(
        self,
        requirements: RequirementSet,
        primary: Sequence[DispatchCandidate],
        coverage: Sequence[CapabilityCoverage],
    ) -> float:
        mandatory = [c for c in coverage if c.mandatory]
        if mandatory:
            coverage_ratio = sum(
                min(1.0, c.provided / c.required) if c.required else 1.0
                for c in mandatory
            ) / len(mandatory)
        else:
            coverage_ratio = 1.0
        target = requirements.recommended_units or requirements.minimum_units
        unit_ratio = min(1.0, len(primary) / target) if target else (
            1.0 if primary else 0.0
        )
        mean_score = (
            sum(c.score_value for c in primary) / len(primary) if primary else 0.0
        )
        return (coverage_ratio + unit_ratio + mean_score) / 3.0

    def _confidence_label(self, score: float) -> ConfidenceLevel:
        thresholds = self._config.confidence
        if score >= thresholds.high:
            return ConfidenceLevel.HIGH
        if score >= thresholds.medium:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW

    @staticmethod
    def _status(
        sufficient: bool, primary_count: int, total_candidates: int
    ) -> DispatchStatus:
        if primary_count == 0:
            return DispatchStatus.NO_RESOURCES
        return DispatchStatus.RECOMMENDED if sufficient else DispatchStatus.PARTIAL
