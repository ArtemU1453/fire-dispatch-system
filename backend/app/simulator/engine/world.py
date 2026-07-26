"""In-memory simulated world (Stage 17).

The world holds *simulated* units and incidents that exist only for the duration
of a training session, in process memory. It is deliberately **decoupled from the
production database and models** — no SQLAlchemy, no real ``Incident`` or unit
rows are read or written. This is the core of the "training contour is fully
isolated from the live system" guarantee.

Positions use an abstract planar coordinate (x, y in kilometres) so distance and
travel time are computed without any GIS dependency.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from app.simulator.engine.enums import (
    SimIncidentStatus,
    SimIncidentType,
    SimUnitCategory,
    SimUnitStatus,
    Weather,
)


@dataclass
class SimUnit:
    """A simulated response unit."""

    id: str
    name: str
    category: SimUnitCategory
    x: float
    y: float
    speed_kmh: float = 50.0
    status: SimUnitStatus = SimUnitStatus.AVAILABLE
    assigned_incident_id: str | None = None

    @property
    def dispatchable(self) -> bool:
        return self.status == SimUnitStatus.AVAILABLE


@dataclass
class SimIncident:
    """A simulated incident presented to the trainee."""

    id: str
    type: SimIncidentType
    x: float
    y: float
    severity: int                       # 1 (minor) .. 5 (major/mass)
    required_units: int                 # how many units an adequate response needs
    required_category: SimUnitCategory
    created_at: float                   # sim time (seconds) the incident appeared
    # Seconds within which an adequate dispatch must occur to meet the norm.
    response_deadline_s: float = 120.0
    status: SimIncidentStatus = SimIncidentStatus.PENDING
    dispatched_unit_ids: list[str] = field(default_factory=list)
    dispatched_at: float | None = None
    resolved_at: float | None = None
    is_false_alarm: bool = False
    label: str = ""


@dataclass
class WorldState:
    """The full mutable state of a simulation at a point in sim time."""

    units: dict[str, SimUnit] = field(default_factory=dict)
    incidents: dict[str, SimIncident] = field(default_factory=dict)
    closed_roads: set[str] = field(default_factory=set)
    weather: Weather = Weather.CLEAR

    # -- units ---------------------------------------------------------------
    def add_unit(self, unit: SimUnit) -> SimUnit:
        self.units[unit.id] = unit
        return unit

    def available_units(
        self, category: SimUnitCategory | None = None
    ) -> list[SimUnit]:
        return [
            u
            for u in self.units.values()
            if u.dispatchable and (category is None or u.category == category)
        ]

    # -- incidents -----------------------------------------------------------
    def add_incident(self, incident: SimIncident) -> SimIncident:
        self.incidents[incident.id] = incident
        return incident

    def pending_incidents(self) -> list[SimIncident]:
        return [
            i
            for i in self.incidents.values()
            if i.status == SimIncidentStatus.PENDING
        ]

    def active_incidents(self) -> list[SimIncident]:
        return [
            i
            for i in self.incidents.values()
            if i.status in (SimIncidentStatus.PENDING, SimIncidentStatus.DISPATCHED)
        ]


def distance_km(ax: float, ay: float, bx: float, by: float) -> float:
    """Planar Euclidean distance in the abstract training coordinate space."""
    return math.hypot(ax - bx, ay - by)


def travel_time_s(
    unit: SimUnit, ix: float, iy: float, road_factor: float = 1.3
) -> float:
    """Estimated travel time (seconds) for a unit to reach an incident.

    Straight-line distance inflated by a road factor, divided by the unit speed.
    Self-contained — no routing/GIS provider involved.
    """
    d = distance_km(unit.x, unit.y, ix, iy) * road_factor
    if unit.speed_kmh <= 0:
        return math.inf
    return (d / unit.speed_kmh) * 3600.0
