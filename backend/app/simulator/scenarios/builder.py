"""Turn scenarios into engines and build scenarios from generators (Stage 17)."""

from __future__ import annotations

from app.simulator.engine.clock import SimulationClock
from app.simulator.engine.engine import Engine
from app.simulator.engine.enums import EventType, SimUnitCategory
from app.simulator.engine.world import SimUnit, WorldState
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
from app.simulator.scenarios.schema import (
    Scenario,
    ScenarioEvent,
    ScenarioUnit,
)


def engine_from_scenario(scenario: Scenario, *, speed: float = 1.0) -> Engine:
    """Instantiate a fresh, deterministic engine for a scenario."""
    world = WorldState()
    for u in scenario.units:
        world.add_unit(
            SimUnit(
                id=u.id,
                name=u.name,
                category=SimUnitCategory(u.category),
                x=u.x,
                y=u.y,
                speed_kmh=u.speed_kmh,
            )
        )
    queue = EventQueue(
        ScheduledEvent(
            time_s=e.time_s,
            type=EventType(e.type),
            payload=dict(e.payload),
            id=e.id,
        )
        for e in scenario.events
    )
    return Engine(world=world, clock=SimulationClock(speed=speed), queue=queue)


def scenario_from_generators(
    *,
    id: str,
    title: str,
    description: str,
    mode: str,
    seed: int = 0,
    duration_s: float = 1800.0,
    incidents: IncidentGenConfig | None = None,
    fleet: FleetConfig | None = None,
    disturbances: DisturbanceConfig | None = None,
    objectives: list[str] | None = None,
) -> Scenario:
    """Assemble a scenario from the incident/unit generators (free modelling)."""
    fleet_cfg = fleet or FleetConfig(seed=seed)
    inc_cfg = incidents or IncidentGenConfig(seed=seed, horizon_s=duration_s)
    units = UnitGenerator().build_fleet(fleet_cfg)
    inc_events = IncidentGenerator(inc_cfg).generate()
    dist_events = (
        UnitGenerator().disturbances([u.id for u in units], disturbances)
        if disturbances
        else []
    )
    all_events = sorted(inc_events + dist_events, key=lambda e: e.time_s)

    scenario_units = [
        ScenarioUnit(
            id=u.id, name=u.name, category=u.category.value,
            x=u.x, y=u.y, speed_kmh=u.speed_kmh,
        )
        for u in units
    ]
    scenario_events = [
        ScenarioEvent(time_s=e.time_s, type=e.type.value, payload=e.payload, id=e.id)
        for e in all_events
    ]
    spawn_count = sum(
        1 for e in all_events if e.type == EventType.SPAWN_INCIDENT
    )
    real_incidents = sum(
        1
        for e in all_events
        if e.type == EventType.SPAWN_INCIDENT
        and not e.payload.get("is_false_alarm")
    )
    from app.simulator.scenarios.schema import ExpectedResult

    return Scenario(
        id=id,
        title=title,
        description=description,
        mode=mode,
        objectives=objectives or [],
        seed=seed,
        duration_s=duration_s,
        units=scenario_units,
        events=scenario_events,
        expected=ExpectedResult(
            resolved_incidents=real_incidents,
            max_expired_incidents=max(0, spawn_count // 5),
        ),
    )
