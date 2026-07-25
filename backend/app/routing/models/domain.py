"""Domain models for routing and ETA (provider-agnostic value objects).

These are plain, immutable-ish value objects — not ORM tables. Routing produces
transient results (a route between two points, a distance, an ETA); persistence
at this stage is limited to an in-memory cache (see ``repositories``). Every
concrete provider maps its own response shape onto these types, so the rest of
the system sees one consistent model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class TravelProfile(str, Enum):
    """The mode of travel a route is planned for."""

    DRIVING = "driving"          # the only profile used at this stage
    WALKING = "walking"
    CYCLING = "cycling"


@dataclass(frozen=True, slots=True)
class GeoPoint:
    """A WGS84 coordinate (latitude, longitude)."""

    latitude: float
    longitude: float

    def as_tuple(self) -> tuple[float, float]:
        return (self.latitude, self.longitude)


@dataclass(frozen=True, slots=True)
class RoutePoint:
    """A single point along a route's geometry (optionally a named waypoint)."""

    latitude: float
    longitude: float
    name: str | None = None
    is_waypoint: bool = False


@dataclass(slots=True)
class RouteSegment:
    """A leg of a route between two consecutive waypoints."""

    start: GeoPoint
    end: GeoPoint
    distance_meters: float
    duration_seconds: float
    geometry: list[RoutePoint] = field(default_factory=list)


@dataclass(slots=True)
class Route:
    """A full route between an origin and a destination."""

    origin: GeoPoint
    destination: GeoPoint
    distance_meters: float
    duration_seconds: float
    provider: str
    profile: TravelProfile = TravelProfile.DRIVING
    segments: list[RouteSegment] = field(default_factory=list)
    geometry: list[RoutePoint] = field(default_factory=list)
    is_fallback: bool = False
    created_at: datetime = field(
        default_factory=lambda: datetime.now(tz=UTC)
    )

    @property
    def waypoints(self) -> list[RoutePoint]:
        """The control points of the route (origin, segment ends, destination)."""
        return [p for p in self.geometry if p.is_waypoint] or [
            RoutePoint(self.origin.latitude, self.origin.longitude, is_waypoint=True),
            RoutePoint(
                self.destination.latitude,
                self.destination.longitude,
                is_waypoint=True,
            ),
        ]


@dataclass(slots=True)
class ETAResult:
    """The estimated time of arrival between two points."""

    origin: GeoPoint
    destination: GeoPoint
    eta_seconds: float
    distance_meters: float
    provider: str
    is_fallback: bool = False

    @property
    def eta_minutes(self) -> float:
        return round(self.eta_seconds / 60.0, 2)


@dataclass(slots=True)
class DistanceResult:
    """The travel distance between two points."""

    origin: GeoPoint
    destination: GeoPoint
    distance_meters: float
    provider: str
    is_fallback: bool = False

    @property
    def distance_km(self) -> float:
        return round(self.distance_meters / 1000.0, 3)


@dataclass(slots=True)
class RoutingRequest:
    """A normalized routing request (origin → destination)."""

    origin: GeoPoint
    destination: GeoPoint
    profile: TravelProfile = TravelProfile.DRIVING
    alternatives: bool = False


@dataclass(slots=True)
class RoutingResponse:
    """The internal envelope carrying a route plus provider metadata."""

    route: Route
    provider: str
    response_time_ms: float
    is_fallback: bool = False


@dataclass(frozen=True, slots=True)
class ProviderHealth:
    """The result of a provider ``health_check``."""

    provider: str
    healthy: bool
    detail: str | None = None
    latency_ms: float | None = None
