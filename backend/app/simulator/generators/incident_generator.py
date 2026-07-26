"""Incident generator (Stage 17 §3).

Produces a deterministic (seeded) stream of ``SPAWN_INCIDENT`` events modelling
fires, traffic accidents, technogenic accidents, false alarms and — as patterns
— simultaneous and mass incidents. Deterministic seeding means an exercise can
be reproduced exactly.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from app.simulator.engine.enums import (
    EventType,
    SimIncidentType,
    SimUnitCategory,
)
from app.simulator.events.definitions import ScheduledEvent

# Which unit category handles which incident type.
_CATEGORY_FOR = {
    SimIncidentType.FIRE: SimUnitCategory.FIRE,
    SimIncidentType.TRAFFIC_ACCIDENT: SimUnitCategory.RESCUE,
    SimIncidentType.TECHNOGENIC: SimUnitCategory.SPECIAL,
    SimIncidentType.FALSE_ALARM: SimUnitCategory.FIRE,
    SimIncidentType.HAZMAT: SimUnitCategory.HAZMAT,
    SimIncidentType.RESCUE: SimUnitCategory.RESCUE,
}


@dataclass
class IncidentGenConfig:
    seed: int = 0
    count: int = 5                       # number of incidents to schedule
    horizon_s: float = 1800.0            # spread incidents across this window
    area_km: float = 20.0               # incidents fall within [0, area_km]^2
    types: list[SimIncidentType] = field(
        default_factory=lambda: [
            SimIncidentType.FIRE,
            SimIncidentType.TRAFFIC_ACCIDENT,
            SimIncidentType.TECHNOGENIC,
            SimIncidentType.FALSE_ALARM,
        ]
    )
    false_alarm_rate: float = 0.15
    max_severity: int = 3
    # Patterns
    simultaneous: int = 0                # N incidents that appear at the same time
    mass_incident: bool = False          # one large multi-unit incident


class IncidentGenerator:
    def __init__(self, config: IncidentGenConfig | None = None) -> None:
        self.config = config or IncidentGenConfig()

    def generate(self) -> list[ScheduledEvent]:
        cfg = self.config
        rng = random.Random(cfg.seed)
        events: list[ScheduledEvent] = []
        n = 0

        def spawn(time_s: float, *, severity: int | None = None,
                  itype: SimIncidentType | None = None,
                  required_units: int | None = None) -> None:
            nonlocal n
            itype = itype or rng.choice(cfg.types)
            is_false = (
                itype == SimIncidentType.FALSE_ALARM
                or rng.random() < cfg.false_alarm_rate
            )
            sev = severity if severity is not None else rng.randint(1, cfg.max_severity)
            req = required_units if required_units is not None else max(1, sev)
            events.append(
                ScheduledEvent(
                    time_s=round(time_s, 1),
                    type=EventType.SPAWN_INCIDENT,
                    id=f"gen-inc-{n}",
                    payload={
                        "id": f"INC{n:03d}",
                        "type": itype.value,
                        "x": round(rng.uniform(0, cfg.area_km), 3),
                        "y": round(rng.uniform(0, cfg.area_km), 3),
                        "severity": 1 if is_false else sev,
                        "required_units": 0 if is_false else req,
                        "required_category": _CATEGORY_FOR[itype].value,
                        "response_deadline_s": 90.0 if is_false else 120.0 + sev * 30,
                        "is_false_alarm": is_false,
                        "label": itype.value,
                    },
                )
            )
            n += 1

        # Baseline stream spread across the horizon.
        for _ in range(cfg.count):
            spawn(rng.uniform(0, cfg.horizon_s))

        # Simultaneous burst: several incidents at one instant (§3).
        if cfg.simultaneous > 0:
            t = rng.uniform(0, cfg.horizon_s * 0.5)
            for _ in range(cfg.simultaneous):
                spawn(t)

        # Mass incident: one severe, multi-unit event (§3).
        if cfg.mass_incident:
            spawn(
                rng.uniform(0, cfg.horizon_s * 0.6),
                severity=5,
                itype=SimIncidentType.FIRE,
                required_units=4,
            )

        events.sort(key=lambda e: e.time_s)
        return events
