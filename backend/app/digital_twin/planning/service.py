"""Digital Twin planning facade (Stage 18).

The single entry point the API talks to. It owns the baseline model (a copy used
for analysis), the scenario store and an in-memory results registry, and it
coordinates coverage analysis, scenario simulation, placement comparison,
forecasting and report generation. It never touches the production database.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from app.digital_twin.coverage.analyzer import CoverageAnalyzer, CoverageResult
from app.digital_twin.forecast.service import ForecastConfig, ForecastService
from app.digital_twin.optimization.optimizer import (
    Optimizer,
    PlacementCandidate,
    PlacementEvaluation,
)
from app.digital_twin.reports.report_builder import (
    AnalyticalReport,
    build_analytical_report,
)
from app.digital_twin.reports.report_builder import _impact as _impact_of
from app.digital_twin.scenarios.library import built_in_scenarios
from app.digital_twin.scenarios.schema import Scenario
from app.digital_twin.scenarios.store import InMemoryScenarioStore, ScenarioStore
from app.digital_twin.simulation.apply import apply_scenario
from app.digital_twin.simulation.model import TwinModel, sample_model


@dataclass
class SimulationResult:
    id: str
    scenario_id: str
    scenario_title: str
    created_at: datetime
    baseline: dict
    scenario: dict
    impact: dict


@dataclass
class ResultsRegistry:
    _items: dict[str, SimulationResult] = field(default_factory=dict)

    def add(self, result: SimulationResult) -> SimulationResult:
        self._items[result.id] = result
        return result

    def get(self, result_id: str) -> SimulationResult | None:
        return self._items.get(result_id)

    def list(self) -> list[SimulationResult]:
        return sorted(self._items.values(), key=lambda r: r.created_at)


class DigitalTwinService:
    def __init__(
        self,
        baseline: TwinModel | None = None,
        store: ScenarioStore | None = None,
        analyzer: CoverageAnalyzer | None = None,
    ) -> None:
        # A copy is held so the reference model is never mutated by callers.
        self._baseline = (baseline or sample_model()).copy(name="baseline")
        self._store: ScenarioStore = store or InMemoryScenarioStore(
            seed=built_in_scenarios()
        )
        self._analyzer = analyzer or CoverageAnalyzer()
        self._optimizer = Optimizer(self._analyzer)
        self._results = ResultsRegistry()

    # ----------------------------------------------------------- scenarios
    def list_scenarios(self) -> list[Scenario]:
        return self._store.list()

    def get_scenario(self, scenario_id: str) -> Scenario:
        return self._store.get(scenario_id)

    def create_scenario(self, scenario: Scenario) -> Scenario:
        return self._store.save(scenario)

    # ------------------------------------------------------------ coverage
    def coverage(self, scenario_id: str | None = None) -> CoverageResult:
        model = self._model_for(scenario_id)
        return self._analyzer.analyze(model)

    def _model_for(self, scenario_id: str | None) -> TwinModel:
        if scenario_id is None:
            return self._baseline
        scenario = self._store.get(scenario_id)
        return apply_scenario(self._baseline, scenario)

    # ------------------------------------------------------------ simulate
    def simulate(self, scenario_id: str) -> SimulationResult:
        scenario = self._store.get(scenario_id)
        base_cov = self._analyzer.analyze(self._baseline)
        scen_cov = self._analyzer.analyze(apply_scenario(self._baseline, scenario))
        impact = _impact_of(base_cov, scen_cov, scenario.id)
        result = SimulationResult(
            id=uuid4().hex,
            scenario_id=scenario.id,
            scenario_title=scenario.title,
            created_at=datetime.now(tz=UTC),
            baseline=base_cov.to_dict(),
            scenario=scen_cov.to_dict(),
            impact=impact.__dict__,
        )
        return self._results.add(result)

    def results(self, result_id: str | None = None) -> list[SimulationResult]:
        if result_id is not None:
            r = self._results.get(result_id)
            return [r] if r else []
        return self._results.list()

    # -------------------------------------------------------- optimization
    def evaluate_placements(
        self, candidates: list[PlacementCandidate]
    ) -> list[PlacementEvaluation]:
        return self._optimizer.evaluate_placements(self._baseline, candidates)

    # ------------------------------------------------------------ forecast
    def forecast(self, config: ForecastConfig):
        return ForecastService().forecast(self._baseline, config)

    # ------------------------------------------------------------- reports
    def report(self, scenario_ids: list[str] | None = None) -> AnalyticalReport:
        if scenario_ids is None:
            scenarios = self._store.list()
        else:
            scenarios = [self._store.get(sid) for sid in scenario_ids]
        return build_analytical_report(
            self._baseline, scenarios, analyzer=self._analyzer
        )

    # --------------------------------------------------------------- model
    @property
    def baseline(self) -> TwinModel:
        return self._baseline
