"""Digital model of the operational system (Stage 18 §2).

An in-memory ("digital twin") model of stations, response districts, the road
network, water sources, protected objects and the operational situation. It is a
**copy** used purely for strategic analysis — it is never connected to the
production database and never modifies live data. Coordinates use an abstract
planar system (x, y in kilometres), so analysis is self-contained (no GIS).
"""

from __future__ import annotations

import copy
import enum
import math
from dataclasses import dataclass, field


class StationCategory(str, enum.Enum):
    FIRE = "fire"
    RESCUE = "rescue"
    MIXED = "mixed"


@dataclass
class Station:
    """A fire/rescue station (подразделение)."""

    id: str
    name: str
    x: float
    y: float
    category: StationCategory = StationCategory.FIRE
    units: int = 1
    active: bool = True


@dataclass
class District:
    """A response district (район выезда) represented by its centroid."""

    id: str
    name: str
    x: float
    y: float
    population: int = 0
    area_km2: float = 1.0
    risk_weight: float = 1.0        # demand weight for coverage aggregation
    norm_time_s: float = 600.0      # response-time norm (норматив выезда)


@dataclass
class RoadNetwork:
    """Simplified road model: speed and a detour factor, both tunable."""

    base_speed_kmh: float = 50.0
    road_factor: float = 1.3        # straight-line → road distance inflation
    speed_multiplier: float = 1.0   # global condition factor (scenarios adjust)

    def travel_time_s(self, ax: float, ay: float, bx: float, by: float) -> float:
        d = math.hypot(ax - bx, ay - by) * self.road_factor
        speed = self.base_speed_kmh * self.speed_multiplier
        if speed <= 0:
            return math.inf
        return (d / speed) * 3600.0


@dataclass
class WaterSource:
    id: str
    x: float
    y: float
    capacity_lps: float = 40.0      # litres per second


@dataclass
class ProtectedObject:
    """An object of protection (объект защиты) with a risk class."""

    id: str
    name: str
    x: float
    y: float
    risk_class: int = 1             # 1 (low) .. 5 (critical)


@dataclass
class OperationalSituation:
    """Coarse operational context used by forecasting/analysis."""

    calls_per_day: float = 50.0
    population_total: int = 0


@dataclass
class TwinModel:
    """The full digital model — a self-contained copy of the operational system."""

    name: str = "baseline"
    area_km: float = 30.0
    stations: dict[str, Station] = field(default_factory=dict)
    districts: dict[str, District] = field(default_factory=dict)
    water_sources: dict[str, WaterSource] = field(default_factory=dict)
    protected_objects: dict[str, ProtectedObject] = field(default_factory=dict)
    road: RoadNetwork = field(default_factory=RoadNetwork)
    situation: OperationalSituation = field(default_factory=OperationalSituation)

    def copy(self, *, name: str | None = None) -> TwinModel:
        """Return a deep, independent copy (so scenarios never touch the base)."""
        clone = copy.deepcopy(self)
        if name is not None:
            clone.name = name
        return clone

    def active_stations(self) -> list[Station]:
        return [s for s in self.stations.values() if s.active]


def sample_model() -> TwinModel:
    """A small, deterministic demo model used as the default baseline and in tests."""
    model = TwinModel(name="baseline", area_km=30.0)
    for s in [
        Station("S1", "ПЧ-1 Центр", 10, 10, StationCategory.FIRE, units=2),
        Station("S2", "ПЧ-2 Север", 10, 24, StationCategory.MIXED, units=1),
        Station("S3", "ПЧ-3 Восток", 24, 12, StationCategory.FIRE, units=1),
    ]:
        model.stations[s.id] = s
    for d in [
        District("D1", "Центральный", 11, 11, population=40000, area_km2=20,
                 risk_weight=1.5, norm_time_s=600),
        District("D2", "Северный", 9, 25, population=25000, area_km2=25,
                 risk_weight=1.0, norm_time_s=600),
        District("D3", "Восточный", 25, 13, population=18000, area_km2=22,
                 risk_weight=1.0, norm_time_s=720),
        District("D4", "Южный", 14, 3, population=12000, area_km2=30,
                 risk_weight=1.2, norm_time_s=720),
        District("D5", "Западный", 2, 16, population=9000, area_km2=28,
                 risk_weight=0.8, norm_time_s=900),
    ]:
        model.districts[d.id] = d
    for w in [
        WaterSource("W1", 10, 12, 60),
        WaterSource("W2", 23, 12, 40),
        WaterSource("W3", 12, 4, 30),
    ]:
        model.water_sources[w.id] = w
    for o in [
        ProtectedObject("O1", "Больница", 11, 12, risk_class=5),
        ProtectedObject("O2", "Школа", 9, 24, risk_class=4),
        ProtectedObject("O3", "Склад ГСМ", 26, 13, risk_class=5),
        ProtectedObject("O4", "ТЦ", 14, 4, risk_class=3),
    ]:
        model.protected_objects[o.id] = o
    model.situation = OperationalSituation(
        calls_per_day=60.0,
        population_total=sum(d.population for d in model.districts.values()),
    )
    return model
