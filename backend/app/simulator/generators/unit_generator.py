"""Unit & environment generator (Stage 17 §4).

Builds a simulated fleet and a deterministic stream of condition events that
model availability, busyness, breakdowns, road closures, weather changes and
resource unavailability — the disturbances a dispatcher must cope with.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from app.simulator.engine.enums import EventType, SimUnitCategory, Weather
from app.simulator.engine.world import SimUnit
from app.simulator.events.definitions import ScheduledEvent


@dataclass
class FleetConfig:
    seed: int = 0
    area_km: float = 20.0
    # How many units of each category to create.
    counts: dict[SimUnitCategory, int] = field(
        default_factory=lambda: {
            SimUnitCategory.FIRE: 4,
            SimUnitCategory.RESCUE: 2,
            SimUnitCategory.MEDICAL: 2,
            SimUnitCategory.HAZMAT: 1,
            SimUnitCategory.SPECIAL: 1,
        }
    )


@dataclass
class DisturbanceConfig:
    seed: int = 0
    horizon_s: float = 1800.0
    breakdowns: int = 0             # поломки техники
    unavailabilities: int = 0       # временная недоступность ресурса
    road_closures: int = 0          # закрытие дорог
    weather_changes: list[Weather] = field(default_factory=list)


class UnitGenerator:
    def build_fleet(self, config: FleetConfig | None = None) -> list[SimUnit]:
        cfg = config or FleetConfig()
        rng = random.Random(cfg.seed)
        units: list[SimUnit] = []
        idx = 0
        prefixes = {
            SimUnitCategory.FIRE: "АЦ",
            SimUnitCategory.RESCUE: "АСМ",
            SimUnitCategory.MEDICAL: "СМП",
            SimUnitCategory.HAZMAT: "ГЗ",
            SimUnitCategory.SPECIAL: "СТ",
        }
        for category, count in cfg.counts.items():
            for i in range(count):
                units.append(
                    SimUnit(
                        id=f"U{idx:03d}",
                        name=f"{prefixes[category]}-{i + 1}",
                        category=category,
                        x=round(rng.uniform(0, cfg.area_km), 3),
                        y=round(rng.uniform(0, cfg.area_km), 3),
                        speed_kmh=round(rng.uniform(40, 60), 1),
                    )
                )
                idx += 1
        return units

    def disturbances(
        self, unit_ids: list[str], config: DisturbanceConfig | None = None
    ) -> list[ScheduledEvent]:
        cfg = config or DisturbanceConfig()
        rng = random.Random(cfg.seed)
        events: list[ScheduledEvent] = []
        n = 0

        def at() -> float:
            return round(rng.uniform(0, cfg.horizon_s * 0.7), 1)

        pool = list(unit_ids)
        rng.shuffle(pool)

        # Breakdowns (with a later repair), then unavailability windows.
        for _ in range(min(cfg.breakdowns, len(pool))):
            uid = pool[n % len(pool)] if pool else None
            if uid is None:
                break
            t = at()
            events.append(ScheduledEvent(t, type=EventType.UNIT_BREAKDOWN,
                                         id=f"brk-{n}", payload={"unit_id": uid}))
            events.append(ScheduledEvent(round(t + rng.uniform(300, 900), 1),
                                         type=EventType.UNIT_REPAIR,
                                         id=f"rep-{n}", payload={"unit_id": uid}))
            n += 1

        for _ in range(cfg.unavailabilities):
            if not pool:
                break
            uid = rng.choice(pool)
            t = at()
            events.append(ScheduledEvent(t, type=EventType.UNIT_UNAVAILABLE,
                                         id=f"un-{n}", payload={"unit_id": uid}))
            events.append(ScheduledEvent(round(t + rng.uniform(300, 900), 1),
                                         type=EventType.UNIT_AVAILABLE,
                                         id=f"av-{n}", payload={"unit_id": uid}))
            n += 1

        for i in range(cfg.road_closures):
            t = at()
            events.append(ScheduledEvent(t, type=EventType.ROAD_CLOSURE,
                                         id=f"rc-{i}", payload={"road": f"R{i}"}))
            events.append(ScheduledEvent(round(t + rng.uniform(600, 1200), 1),
                                         type=EventType.ROAD_REOPEN,
                                         id=f"ro-{i}", payload={"road": f"R{i}"}))

        for i, weather in enumerate(cfg.weather_changes):
            events.append(ScheduledEvent(at(), type=EventType.WEATHER_CHANGE,
                                         id=f"wx-{i}",
                                         payload={"weather": weather.value}))

        events.sort(key=lambda e: e.time_s)
        return events
