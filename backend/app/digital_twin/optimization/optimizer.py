"""Placement & scenario comparison (Stage 18 §5).

Evaluates different station-placement options and different scenarios and
produces **comparative metrics** — it never applies a change or decides
anything automatically (per the stage constraint). The output is decision
support for a human analyst.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.digital_twin.coverage.analyzer import CoverageAnalyzer, CoverageResult
from app.digital_twin.scenarios.schema import (
    Modification,
    ModificationType,
    Scenario,
)
from app.digital_twin.simulation.apply import apply_scenario
from app.digital_twin.simulation.model import TwinModel


@dataclass
class PlacementCandidate:
    id: str
    name: str
    x: float
    y: float
    units: int = 1


@dataclass
class PlacementEvaluation:
    candidate_id: str
    name: str
    x: float
    y: float
    population_covered_pct: float
    territory_covered_pct: float
    delta_population_pct: float
    delta_territory_pct: float
    unreachable_after: list[str] = field(default_factory=list)


@dataclass
class ScenarioComparison:
    scenario_id: str
    title: str
    population_covered_pct: float
    territory_covered_pct: float
    avg_arrival_time_s: float | None
    delta_population_pct: float
    delta_territory_pct: float
    unreachable_districts: list[str] = field(default_factory=list)
    risk_zones: list[str] = field(default_factory=list)


class Optimizer:
    def __init__(self, analyzer: CoverageAnalyzer | None = None) -> None:
        self._analyzer = analyzer or CoverageAnalyzer()

    # ---------------------------------------------------------- placements
    def evaluate_placements(
        self, baseline: TwinModel, candidates: list[PlacementCandidate]
    ) -> list[PlacementEvaluation]:
        """Score each candidate location by the coverage it would add.

        Purely comparative — the baseline is never modified and nothing is
        applied; each candidate is scored on an independent copy.
        """
        base_cov = self._analyzer.analyze(baseline)
        evaluations: list[PlacementEvaluation] = []
        for cand in candidates:
            scenario = Scenario(
                id=f"placement-{cand.id}",
                title=f"Placement {cand.name}",
                modifications=[
                    Modification(
                        type=ModificationType.OPEN_STATION.value,
                        params={"id": f"CAND-{cand.id}", "name": cand.name,
                                "x": cand.x, "y": cand.y, "units": cand.units},
                    )
                ],
            )
            model = apply_scenario(baseline, scenario)
            cov = self._analyzer.analyze(model)
            evaluations.append(
                PlacementEvaluation(
                    candidate_id=cand.id,
                    name=cand.name,
                    x=cand.x,
                    y=cand.y,
                    population_covered_pct=cov.population_covered_pct,
                    territory_covered_pct=cov.territory_covered_pct,
                    delta_population_pct=round(
                        cov.population_covered_pct - base_cov.population_covered_pct, 1
                    ),
                    delta_territory_pct=round(
                        cov.territory_covered_pct - base_cov.territory_covered_pct, 1
                    ),
                    unreachable_after=cov.unreachable_districts,
                )
            )
        # Best coverage gain first — a ranking for the analyst, not a decision.
        evaluations.sort(
            key=lambda e: (e.delta_population_pct, e.delta_territory_pct),
            reverse=True,
        )
        return evaluations

    # ------------------------------------------------------------ scenarios
    def compare_scenarios(
        self, baseline: TwinModel, scenarios: list[Scenario]
    ) -> tuple[CoverageResult, list[ScenarioComparison]]:
        base = self._analyzer.analyze(baseline)
        rows: list[ScenarioComparison] = []
        for sc in scenarios:
            model = apply_scenario(baseline, sc)
            cov = self._analyzer.analyze(model)
            rows.append(
                ScenarioComparison(
                    scenario_id=sc.id,
                    title=sc.title,
                    population_covered_pct=cov.population_covered_pct,
                    territory_covered_pct=cov.territory_covered_pct,
                    avg_arrival_time_s=cov.avg_arrival_time_s,
                    delta_population_pct=round(
                        cov.population_covered_pct - base.population_covered_pct, 1
                    ),
                    delta_territory_pct=round(
                        cov.territory_covered_pct - base.territory_covered_pct, 1
                    ),
                    unreachable_districts=cov.unreachable_districts,
                    risk_zones=cov.risk_zones,
                )
            )
        return base, rows
