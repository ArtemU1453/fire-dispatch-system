"""Analytical reports (Stage 18 §7).

Builds the materials a leadership audience needs: coverage maps, risk maps,
scenario comparison, impact assessment and a written justification of proposals.
Everything is derived from copies of the model — nothing is written back.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.digital_twin.coverage.analyzer import (
    CoverageAnalyzer,
    CoverageResult,
    coverage_map,
)
from app.digital_twin.optimization.optimizer import Optimizer, ScenarioComparison
from app.digital_twin.scenarios.schema import Scenario
from app.digital_twin.simulation.apply import apply_scenario
from app.digital_twin.simulation.model import TwinModel


@dataclass
class CoverageMapReport:
    grid_step_km: float
    norm_s: float
    covered_pct: float
    cells: list[dict] = field(default_factory=list)


@dataclass
class RiskMapReport:
    objects: list[dict] = field(default_factory=list)
    uncovered_high_risk: list[str] = field(default_factory=list)


@dataclass
class ImpactAssessment:
    scenario_id: str
    delta_population_pct: float
    delta_territory_pct: float
    newly_covered_districts: list[str] = field(default_factory=list)
    newly_uncovered_districts: list[str] = field(default_factory=list)
    verdict: str = ""


@dataclass
class AnalyticalReport:
    baseline: dict
    coverage_map: dict
    risk_map: dict
    scenario_comparison: list[dict] = field(default_factory=list)
    impact: list[dict] = field(default_factory=list)
    justification: list[str] = field(default_factory=list)


def build_coverage_map(
    model: TwinModel, *, grid_step_km: float = 3.0, norm_s: float = 600.0
) -> CoverageMapReport:
    cells = coverage_map(model, grid_step_km=grid_step_km, norm_s=norm_s)
    covered = sum(1 for c in cells if c.covered)
    return CoverageMapReport(
        grid_step_km=grid_step_km,
        norm_s=norm_s,
        covered_pct=round(100.0 * covered / len(cells), 1) if cells else 0.0,
        cells=[c.__dict__ for c in cells],
    )


def build_risk_map(model: TwinModel) -> RiskMapReport:
    from app.digital_twin.coverage.analyzer import _nearest

    stations = model.active_stations()
    objects: list[dict] = []
    uncovered: list[str] = []
    for obj in model.protected_objects.values():
        _, t = _nearest(stations, model, obj.x, obj.y)
        strict = 600.0 - (obj.risk_class - 1) * 60.0
        covered = t is not None and t <= strict
        objects.append({
            "id": obj.id, "name": obj.name, "risk_class": obj.risk_class,
            "arrival_time_s": round(t, 1) if t is not None else None,
            "covered": covered,
        })
        if not covered and obj.risk_class >= 4:
            uncovered.append(obj.id)
    return RiskMapReport(objects=objects, uncovered_high_risk=uncovered)


def _impact(
    baseline: CoverageResult, scenario_cov: CoverageResult, scenario_id: str
) -> ImpactAssessment:
    base_unreached = set(baseline.unreachable_districts)
    scen_unreached = set(scenario_cov.unreachable_districts)
    newly_covered = sorted(base_unreached - scen_unreached)
    newly_uncovered = sorted(scen_unreached - base_unreached)
    dpop = round(
        scenario_cov.population_covered_pct - baseline.population_covered_pct, 1
    )
    dterr = round(
        scenario_cov.territory_covered_pct - baseline.territory_covered_pct, 1
    )
    if dpop > 0 or newly_covered:
        verdict = "положительное влияние на покрытие"
    elif dpop < 0 or newly_uncovered:
        verdict = "ухудшение покрытия"
    else:
        verdict = "покрытие практически не изменилось"
    return ImpactAssessment(
        scenario_id=scenario_id,
        delta_population_pct=dpop,
        delta_territory_pct=dterr,
        newly_covered_districts=newly_covered,
        newly_uncovered_districts=newly_uncovered,
        verdict=verdict,
    )


def _justification(rows: list[ScenarioComparison]) -> list[str]:
    if not rows:
        return ["Нет сценариев для сравнения."]
    best = max(rows, key=lambda r: r.delta_population_pct)
    lines: list[str] = []
    if best.delta_population_pct > 0:
        lines.append(
            f"Наибольший прирост покрытия населения даёт сценарий "
            f"«{best.title}» (+{best.delta_population_pct}%). "
            "Рекомендуется к детальной проработке."
        )
    else:
        lines.append(
            "Ни один из рассмотренных сценариев не улучшает покрытие населения; "
            "требуется рассмотреть иные варианты размещения."
        )
    worst = min(rows, key=lambda r: r.delta_population_pct)
    if worst.delta_population_pct < 0:
        lines.append(
            f"Сценарий «{worst.title}» снижает покрытие "
            f"({worst.delta_population_pct}%) — при его реализации потребуются "
            "компенсирующие меры."
        )
    lines.append(
        "Итоговое решение принимает руководство; платформа предоставляет только "
        "сравнительные показатели и обоснование (без автоматических изменений)."
    )
    return lines


def build_analytical_report(
    baseline: TwinModel,
    scenarios: list[Scenario],
    *,
    analyzer: CoverageAnalyzer | None = None,
    grid_step_km: float = 3.0,
) -> AnalyticalReport:
    analyzer = analyzer or CoverageAnalyzer(grid_step_km=grid_step_km)
    optimizer = Optimizer(analyzer)
    base_cov, rows = optimizer.compare_scenarios(baseline, scenarios)

    impacts: list[dict] = []
    for sc in scenarios:
        cov = analyzer.analyze(apply_scenario(baseline, sc))
        impacts.append(_impact(base_cov, cov, sc.id).__dict__)

    return AnalyticalReport(
        baseline=base_cov.to_dict(),
        coverage_map=build_coverage_map(
            baseline, grid_step_km=grid_step_km
        ).__dict__,
        risk_map=build_risk_map(baseline).__dict__,
        scenario_comparison=[r.__dict__ for r in rows],
        impact=impacts,
        justification=_justification(rows),
    )
