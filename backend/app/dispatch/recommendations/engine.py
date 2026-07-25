"""RecommendationEngine — assembles the recommendation for the dispatcher.

Given scored candidates (already ranked) and the incident rule, it selects a
primary composition that meets the required capabilities and unit counts, picks
reserves, checks sufficiency, computes a confidence label and explains every
choice. It never dispatches anything — the output is purely advisory.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.dispatch.algorithms.candidate import DispatchCandidate
from app.dispatch.recommendations.models import (
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    CONFIDENCE_MEDIUM,
    ROLE_PRIMARY,
    ROLE_RESERVE,
    CapabilityCoverage,
    Recommendation,
    RecommendedUnit,
)
from app.dispatch.rules.models import IncidentRule, ScoringConfig


class RecommendationEngine:
    """Builds a :class:`Recommendation` from ranked candidates and a rule."""

    def __init__(self, scoring: ScoringConfig) -> None:
        self._scoring = scoring

    def build(
        self,
        *,
        rule: IncidentRule,
        latitude: float,
        longitude: float,
        candidates: Sequence[DispatchCandidate],
        preview: bool = False,
    ) -> Recommendation:
        primary = self._select_primary(rule, candidates, preview=preview)
        primary_ids = {c.id for c in primary}
        if preview:
            reserve: list[DispatchCandidate] = []
        else:
            spare = [c for c in candidates if c.id not in primary_ids]
            reserve = spare[: rule.reserve_units]

        coverage = self._coverage(rule, primary)
        caps_ok = all(cov.satisfied for cov in coverage)
        units_ok = len(primary) >= rule.minimum_units
        sufficient = caps_ok and units_ok

        confidence_score = self._confidence_score(rule, primary, coverage)
        confidence = self._confidence_label(confidence_score)
        messages = self._messages(rule, primary, coverage, units_ok)

        return Recommendation(
            incident_type=rule.code,
            incident_name=rule.name,
            priority=rule.priority,
            latitude=latitude,
            longitude=longitude,
            primary_units=[self._unit(c, ROLE_PRIMARY) for c in primary],
            reserve_units=[self._unit(c, ROLE_RESERVE) for c in reserve],
            capability_coverage=coverage,
            sufficient=sufficient,
            confidence=confidence,
            confidence_score=round(confidence_score, 4),
            total_candidates=len(candidates),
            messages=messages,
            is_preview=preview,
        )

    # ---------------------------------------------------------- selection
    def _select_primary(
        self,
        rule: IncidentRule,
        candidates: Sequence[DispatchCandidate],
        *,
        preview: bool,
    ) -> list[DispatchCandidate]:
        selected: list[DispatchCandidate] = []
        for candidate in candidates:
            if len(selected) >= rule.recommended_units:
                break
            selected.append(candidate)

        if preview:
            return selected

        # Top-up pass: add candidates that cover a still-missing capability.
        selected_ids = {c.id for c in selected}
        provided = self._provided(rule, selected)
        required = {c.code: c.min_quantity for c in rule.required_capabilities}
        for candidate in candidates:
            if candidate.id in selected_ids:
                continue
            missing = [
                code
                for code, need in required.items()
                if provided.get(code, 0) < need and candidate.capabilities.get(code, 0)
            ]
            if missing:
                selected.append(candidate)
                selected_ids.add(candidate.id)
                for code, qty in candidate.capabilities.items():
                    provided[code] = provided.get(code, 0) + qty
        return selected

    # ---------------------------------------------------------- coverage
    @staticmethod
    def _provided(
        rule: IncidentRule, units: Sequence[DispatchCandidate]
    ) -> dict[str, int]:
        provided: dict[str, int] = {}
        for req in rule.required_capabilities:
            provided[req.code] = sum(u.capabilities.get(req.code, 0) for u in units)
        return provided

    def _coverage(
        self, rule: IncidentRule, units: Sequence[DispatchCandidate]
    ) -> list[CapabilityCoverage]:
        provided = self._provided(rule, units)
        return [
            CapabilityCoverage(
                code=req.code,
                label=req.label,
                required=req.min_quantity,
                provided=provided.get(req.code, 0),
            )
            for req in rule.required_capabilities
        ]

    # ---------------------------------------------------------- confidence
    def _confidence_score(
        self,
        rule: IncidentRule,
        primary: Sequence[DispatchCandidate],
        coverage: Sequence[CapabilityCoverage],
    ) -> float:
        if coverage:
            coverage_ratio = sum(
                min(1.0, c.provided / c.required) for c in coverage
            ) / len(coverage)
        else:
            coverage_ratio = 1.0
        unit_ratio = (
            min(1.0, len(primary) / rule.recommended_units)
            if rule.recommended_units
            else 1.0
        )
        mean_score = (
            sum(c.score_value for c in primary) / len(primary) if primary else 0.0
        )
        return (coverage_ratio + unit_ratio + mean_score) / 3.0

    def _confidence_label(self, score: float) -> str:
        cfg = self._scoring.confidence
        if score >= cfg.high_threshold:
            return CONFIDENCE_HIGH
        if score >= cfg.medium_threshold:
            return CONFIDENCE_MEDIUM
        return CONFIDENCE_LOW

    # ------------------------------------------------------------- output
    @staticmethod
    def _unit(candidate: DispatchCandidate, role: str) -> RecommendedUnit:
        reasons = list(candidate.score.reasons) if candidate.score else []
        return RecommendedUnit(candidate=candidate, role=role, reasons=reasons)

    @staticmethod
    def _messages(
        rule: IncidentRule,
        primary: Sequence[DispatchCandidate],
        coverage: Sequence[CapabilityCoverage],
        units_ok: bool,
    ) -> list[str]:
        messages: list[str] = []
        if not primary:
            messages.append("Доступных ресурсов не найдено.")
            return messages
        if not units_ok:
            messages.append(
                f"Недостаточно единиц: подобрано {len(primary)} из "
                f"минимально необходимых {rule.minimum_units}."
            )
        for cov in coverage:
            if not cov.satisfied:
                messages.append(
                    f"Не покрыта возможность «{cov.label or cov.code}»: "
                    f"{cov.provided} из {cov.required}."
                )
        if not messages:
            messages.append("Рекомендация сформирована; требования выполнены.")
        return messages
