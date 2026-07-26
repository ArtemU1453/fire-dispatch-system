"""Unit tests for the simulation & training platform (Stage 17)."""

from __future__ import annotations

import json

from app.simulator.engine.clock import SimulationClock
from app.simulator.engine.engine import Engine
from app.simulator.engine.enums import (
    EventType,
    SimIncidentStatus,
    SimIncidentType,
    SimUnitCategory,
    SimUnitStatus,
    Weather,
)
from app.simulator.engine.world import SimIncident, SimUnit, travel_time_s
from app.simulator.events.definitions import ScheduledEvent
from app.simulator.events.queue import EventQueue
from app.simulator.generators.incident_generator import (
    IncidentGenConfig,
    IncidentGenerator,
)
from app.simulator.generators.unit_generator import (
    DisturbanceConfig,
    FleetConfig,
    UnitGenerator,
)
from app.simulator.reports.report_builder import build_report
from app.simulator.scenarios.builder import engine_from_scenario
from app.simulator.scenarios.library import built_in_scenarios
from app.simulator.scenarios.schema import Scenario
from app.simulator.scenarios.store import (
    InMemoryScenarioStore,
    ScenarioNotFoundError,
)
from app.simulator.statistics.evaluator import evaluate


# ------------------------------------------------------------------- clock ---
def test_clock_pause_and_step() -> None:
    clock = SimulationClock(speed=1.0, step_seconds=10.0)
    clock.advance(5)
    assert clock.time_s == 5
    clock.pause()
    clock.advance(100)          # ignored while paused
    assert clock.time_s == 5
    clock.step()                # stepping works even while paused
    assert clock.time_s == 15
    clock.resume()
    clock.tick(2)               # 2 real s * speed 1.0
    assert clock.time_s == 17


def test_clock_speed_scaling_and_validation() -> None:
    clock = SimulationClock(speed=4.0)
    clock.tick(10)
    assert clock.time_s == 40
    import pytest

    with pytest.raises(ValueError):
        clock.set_speed(0)


# ------------------------------------------------------------------ engine ---
def _fire_unit(uid: str = "U1", x: float = 0, y: float = 0) -> SimUnit:
    return SimUnit(id=uid, name="AC", category=SimUnitCategory.FIRE, x=x, y=y)


def test_engine_dispatch_resolves_and_frees_unit() -> None:
    eng = Engine()
    eng.seed_units([_fire_unit()])
    eng.queue = EventQueue([
        ScheduledEvent(10, type=EventType.SPAWN_INCIDENT, payload={
            "id": "I1", "type": "fire", "x": 3, "y": 4, "severity": 1,
            "required_units": 1, "required_category": "fire",
        })
    ])
    eng.advance(10)
    assert [i.id for i in eng.world.pending_incidents()] == ["I1"]
    assert eng.dispatch("I1", ["U1"]).accepted
    assert eng.world.units["U1"].status == SimUnitStatus.BUSY
    eng.run_to_end()
    assert eng.world.incidents["I1"].status == SimIncidentStatus.RESOLVED
    assert eng.world.units["U1"].status == SimUnitStatus.AVAILABLE
    assert eng.is_finished


def test_engine_expires_neglected_incident() -> None:
    eng = Engine()
    eng.world.add_incident(SimIncident(
        id="I2", type=SimIncidentType.FIRE, x=0, y=0, severity=1,
        required_units=1, required_category=SimUnitCategory.FIRE,
        created_at=0.0, response_deadline_s=60.0,
    ))
    eng.advance(120)
    assert eng.world.incidents["I2"].status == SimIncidentStatus.EXPIRED


def test_engine_rejects_unknown_and_unavailable() -> None:
    eng = Engine()
    eng.seed_units([_fire_unit()])
    eng.world.add_incident(SimIncident(
        id="I3", type=SimIncidentType.FIRE, x=0, y=0, severity=1,
        required_units=1, required_category=SimUnitCategory.FIRE, created_at=0.0,
    ))
    assert not eng.dispatch("NOPE", ["U1"]).accepted        # unknown incident
    assert not eng.dispatch("I3", ["ZZ"]).accepted          # unknown unit
    eng.world.units["U1"].status = SimUnitStatus.BROKEN
    assert not eng.dispatch("I3", ["U1"]).accepted          # not available


def test_engine_breakdown_event_marks_unit() -> None:
    eng = Engine()
    eng.seed_units([_fire_unit()])
    eng.queue = EventQueue([
        ScheduledEvent(5, type=EventType.UNIT_BREAKDOWN, payload={"unit_id": "U1"}),
        ScheduledEvent(20, type=EventType.WEATHER_CHANGE, payload={"weather": "snow"}),
    ])
    eng.advance(25)
    assert eng.world.units["U1"].status == SimUnitStatus.BROKEN
    assert eng.world.weather == Weather.SNOW


def test_travel_time_scales_with_distance() -> None:
    near = travel_time_s(_fire_unit(x=0, y=0), 1, 0)
    far = travel_time_s(_fire_unit(x=0, y=0), 10, 0)
    assert far > near > 0


# -------------------------------------------------------------- generators ---
def test_incident_generator_is_deterministic() -> None:
    cfg = IncidentGenConfig(seed=42, count=5, simultaneous=2, mass_incident=True)
    a = IncidentGenerator(cfg).generate()
    b = IncidentGenerator(cfg).generate()
    assert [(e.time_s, e.payload["id"]) for e in a] == [
        (e.time_s, e.payload["id"]) for e in b
    ]
    # count + simultaneous burst + mass incident = 5 + 2 + 1
    assert len(a) == 8
    assert any(e.payload["severity"] == 5 for e in a)   # mass incident present


def test_unit_generator_fleet_and_disturbances() -> None:
    units = UnitGenerator().build_fleet(FleetConfig(seed=1))
    assert len(units) == 10
    ids = [u.id for u in units]
    events = UnitGenerator().disturbances(
        ids, DisturbanceConfig(seed=1, breakdowns=1, road_closures=1,
                               weather_changes=[Weather.FOG]),
    )
    types = {e.type for e in events}
    assert EventType.UNIT_BREAKDOWN in types
    assert EventType.UNIT_REPAIR in types           # breakdown pairs with repair
    assert EventType.ROAD_CLOSURE in types
    assert EventType.WEATHER_CHANGE in types


# --------------------------------------------------------------- scenarios ---
def test_scenario_json_round_trip() -> None:
    for scenario in built_in_scenarios():
        data = json.loads(json.dumps(scenario.to_dict(), ensure_ascii=False))
        restored = Scenario.from_dict(data)
        assert restored.id == scenario.id
        assert len(restored.events) == len(scenario.events)
        assert len(restored.units) == len(scenario.units)


def test_scenario_store_crud() -> None:
    store = InMemoryScenarioStore(seed=built_in_scenarios())
    assert len(store.list()) == 3
    import pytest

    with pytest.raises(ScenarioNotFoundError):
        store.get("missing")
    new = Scenario(id="x1", title="X", description="d")
    store.save(new)
    assert store.get("x1").title == "X"
    store.delete("x1")
    with pytest.raises(ScenarioNotFoundError):
        store.get("x1")


def test_file_scenario_store_persists(tmp_path) -> None:
    from app.simulator.scenarios.store import FileScenarioStore

    FileScenarioStore(tmp_path, seed=built_in_scenarios())   # writes files
    reopened = FileScenarioStore(tmp_path)                    # reads them back
    assert {s.id for s in reopened.list()} == {
        "basic-fire-01", "exam-multi-01", "mass-incident-01"
    }


# ---------------------------------------------------------------- scoring ----
def test_evaluation_perfect_run_passes() -> None:
    scenario = built_in_scenarios()[0]
    eng = engine_from_scenario(scenario)
    eng.advance(30)
    inc = eng.world.pending_incidents()[0]
    eng.dispatch(inc.id, ["U000"])          # nearest fire unit, correct category
    eng.run_to_end()
    ev = evaluate(eng, scenario)
    assert ev.passed
    assert ev.correct_pct == 100.0
    assert ev.error_count == 0
    assert ev.score >= scenario.criteria.pass_score


def test_evaluation_penalises_neglect() -> None:
    scenario = built_in_scenarios()[0]
    eng = engine_from_scenario(scenario)
    eng.run_to_end()                        # trainee does nothing → incident expires
    ev = evaluate(eng, scenario)
    assert not ev.passed
    assert ev.expired_incidents >= 1
    assert ev.error_count >= 1


def test_report_contains_metrics_and_recommendations() -> None:
    scenario = built_in_scenarios()[0]
    eng = engine_from_scenario(scenario)
    eng.run_to_end()
    ev = evaluate(eng, scenario)
    report = build_report(
        session_id="S", trainee="t", scenario=scenario, evaluation=ev
    )
    assert report.verdict == "failed"
    assert "error_count" in report.metrics
    assert report.recommendations
    assert "сессия S" in report.to_text()
