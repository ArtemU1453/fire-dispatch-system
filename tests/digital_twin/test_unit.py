"""Unit + scenario tests for the Digital Twin (Stage 18 §11)."""

from __future__ import annotations

import json

from app.digital_twin.coverage.analyzer import CoverageAnalyzer, coverage_map
from app.digital_twin.forecast.models import (
    CompoundGrowthModel,
    LinearGrowthModel,
)
from app.digital_twin.forecast.service import ForecastConfig, ForecastService
from app.digital_twin.optimization.optimizer import Optimizer, PlacementCandidate
from app.digital_twin.reports.report_builder import (
    build_analytical_report,
    build_risk_map,
)
from app.digital_twin.scenarios.library import built_in_scenarios
from app.digital_twin.scenarios.schema import (
    Modification,
    ModificationType,
    Scenario,
)
from app.digital_twin.simulation.apply import (
    ScenarioApplicationError,
    apply_scenario,
)
from app.digital_twin.simulation.model import sample_model


# ------------------------------------------------------------------ model ---
def test_sample_model_has_expected_entities() -> None:
    m = sample_model()
    assert len(m.stations) == 3
    assert len(m.districts) == 5
    assert m.situation.population_total == sum(
        d.population for d in m.districts.values()
    )


def test_model_copy_is_independent() -> None:
    m = sample_model()
    clone = m.copy(name="c")
    clone.stations["S1"].active = False
    clone.road.speed_multiplier = 0.5
    assert m.stations["S1"].active is True      # original untouched
    assert m.road.speed_multiplier == 1.0


# --------------------------------------------------------------- coverage ---
def test_coverage_computes_reachable_and_unreachable() -> None:
    m = sample_model()
    cov = CoverageAnalyzer(grid_step_km=3.0).analyze(m)
    assert 0 <= cov.population_covered_pct <= 100
    assert cov.grid_size > 0
    # central districts are covered; far south/west are not in the sample
    covered = {c.district_id for c in cov.per_district if c.covered}
    assert "D1" in covered
    assert set(cov.unreachable_districts) & {"D4", "D5"}


def test_closing_all_stations_makes_everything_unreachable() -> None:
    m = sample_model()
    for s in m.stations.values():
        s.active = False
    cov = CoverageAnalyzer().analyze(m)
    assert cov.population_covered_pct == 0.0
    assert cov.territory_covered_pct == 0.0
    assert len(cov.unreachable_districts) == len(m.districts)


def test_coverage_map_cells_have_times() -> None:
    m = sample_model()
    cells = coverage_map(m, grid_step_km=5.0)
    assert cells and all(c.arrival_time_s is not None for c in cells)


# ------------------------------------------------------ scenarios / apply ---
def test_apply_open_station_improves_coverage_without_mutating_baseline() -> None:
    base = sample_model()
    an = CoverageAnalyzer(grid_step_km=3.0)
    before = an.analyze(base).population_covered_pct
    scenario = Scenario(
        id="s", title="open",
        modifications=[Modification(
            type=ModificationType.OPEN_STATION.value,
            params={"id": "SX", "name": "Юг", "x": 13, "y": 5},
        )],
    )
    model = apply_scenario(base, scenario)
    after = an.analyze(model).population_covered_pct
    assert after > before
    assert "SX" not in base.stations          # baseline untouched (isolation)
    assert len(base.stations) == 3


def test_apply_close_station_reduces_coverage() -> None:
    base = sample_model()
    an = CoverageAnalyzer(grid_step_km=3.0)
    before = an.analyze(base).population_covered_pct
    scenario = Scenario(
        id="s", title="close",
        modifications=[Modification(
            type=ModificationType.CLOSE_STATION.value, params={"id": "S1"},
        )],
    )
    after = an.analyze(apply_scenario(base, scenario)).population_covered_pct
    assert after < before


def test_apply_unknown_modification_raises() -> None:
    base = sample_model()
    scenario = Scenario(
        id="s", title="bad",
        modifications=[Modification(type="teleport", params={})],
    )
    try:
        apply_scenario(base, scenario)
        raise AssertionError("expected ScenarioApplicationError")
    except ScenarioApplicationError:
        pass


def test_change_norm_and_road_change_apply() -> None:
    base = sample_model()
    scenario = Scenario(
        id="s", title="norm+road",
        modifications=[
            Modification(type=ModificationType.CHANGE_NORM.value,
                         params={"norm_time_s": 300}),
            Modification(type=ModificationType.ROAD_CHANGE.value,
                         params={"speed_multiplier": 0.5}),
        ],
    )
    model = apply_scenario(base, scenario)
    assert all(d.norm_time_s == 300 for d in model.districts.values())
    assert model.road.speed_multiplier == 0.5
    assert base.road.speed_multiplier == 1.0


def test_scenario_json_round_trip() -> None:
    for sc in built_in_scenarios():
        restored = Scenario.from_dict(
            json.loads(json.dumps(sc.to_dict(), ensure_ascii=False))
        )
        assert restored.id == sc.id
        assert len(restored.modifications) == len(sc.modifications)


# ------------------------------------------------------------ optimization ---
def test_placement_evaluation_ranks_by_gain() -> None:
    base = sample_model()
    cands = [
        PlacementCandidate("A", "Юг", 13, 5),
        PlacementCandidate("B", "ДальнийУгол", 29, 29),
    ]
    evals = Optimizer().evaluate_placements(base, cands)
    # ranked best-first; the южный candidate should out-gain the far corner
    assert evals[0].delta_population_pct >= evals[1].delta_population_pct
    assert evals[0].candidate_id == "A"
    # baseline untouched
    assert len(base.stations) == 3


def test_compare_scenarios_produces_deltas() -> None:
    base = sample_model()
    _, rows = Optimizer().compare_scenarios(base, built_in_scenarios())
    assert len(rows) == 4
    open_row = next(r for r in rows if r.scenario_id == "open-south-station")
    assert open_row.delta_population_pct > 0


# --------------------------------------------------------------- forecast ---
def test_linear_and_compound_growth() -> None:
    lin = LinearGrowthModel(0.1).project(100, 2)
    assert [p.value for p in lin] == [100.0, 110.0, 120.0]
    comp = CompoundGrowthModel(0.1).project(100, 2)
    assert comp[2].value == 121.0


def test_forecast_service_projects_and_notes() -> None:
    m = sample_model()
    res = ForecastService().forecast(
        m, ForecastConfig(horizon_years=4, call_growth_rate=0.05)
    )
    assert len(res.calls_per_day) == 5
    assert res.calls_per_day[-1].value > res.calls_per_day[0].value
    assert res.notes


# ----------------------------------------------------------------- reports ---
def test_risk_map_flags_uncovered_high_risk() -> None:
    m = sample_model()
    # Disable all stations so every high-risk object is uncovered.
    for s in m.stations.values():
        s.active = False
    rmap = build_risk_map(m)
    assert rmap.uncovered_high_risk        # some risk>=4 object uncovered


def test_analytical_report_has_all_sections() -> None:
    base = sample_model()
    report = build_analytical_report(base, built_in_scenarios())
    assert report.baseline
    assert report.coverage_map["cells"]
    assert "objects" in report.risk_map
    assert len(report.scenario_comparison) == 4
    assert len(report.impact) == 4
    assert report.justification


def test_report_justification_recommends_best_scenario() -> None:
    base = sample_model()
    report = build_analytical_report(base, built_in_scenarios())
    joined = " ".join(report.justification)
    assert "Открытие подразделения на юге" in joined
