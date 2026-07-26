"""Server-shaped DTOs the mobile BFF serves (Stage 19).

These are the *only* shapes the mobile apps see. They are produced entirely on
the server; the apps contain no business logic and never compute these values
themselves. Kept as plain dataclasses so a provider can build them from any
source (sample data here; the real incident/resource/routing services in
production via the adapter seam).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MobileIncident:
    id: str
    category: str
    priority: str
    status: str
    address: str
    description: str
    lat: float | None
    lon: float | None
    created_at: str
    recommended_units: list[str] = field(default_factory=list)
    assigned_unit_ids: list[str] = field(default_factory=list)


@dataclass
class ResourceLoad:
    unit_id: str
    name: str
    category: str
    status: str
    busy: bool
    lat: float | None = None
    lon: float | None = None


@dataclass
class RoutePoint:
    lat: float
    lon: float


@dataclass
class Route:
    points: list[RoutePoint] = field(default_factory=list)
    distance_km: float = 0.0
    eta_seconds: float | None = None


@dataclass
class DispatchCard:
    incident_id: str
    address: str
    description: str
    category: str
    priority: str
    recommended_composition: list[str] = field(default_factory=list)
    contact: str | None = None
    lat: float | None = None
    lon: float | None = None


@dataclass
class OperationalSummary:
    active_incidents: int
    available_units: int
    busy_units: int
    calls_today: int


@dataclass
class CriticalNotification:
    id: str
    type: str
    message: str
    created_at: str
    incident_id: str | None = None
    severity: str = "critical"
