"""Haversine routing provider — dependency-free straight-line estimator.

Computes a great-circle distance, scales it by a configurable **road factor** to
approximate travel distance, and derives ETA from a configurable **average
speed**. It ignores road geometry, traffic and closures (out of scope for this
stage) but makes the module fully functional and testable without any external
routing server. It is also the default fallback when a real provider (OSRM) is
unavailable.
"""

from __future__ import annotations

from app.routing.interfaces.routing_provider import RoutingProvider
from app.routing.models.domain import (
    DistanceResult,
    ETAResult,
    GeoPoint,
    ProviderHealth,
    Route,
    RoutePoint,
    RouteSegment,
    TravelProfile,
)
from app.routing.utils.geo import haversine_meters


class HaversineRoutingProvider(RoutingProvider):
    """Offline straight-line distance/ETA estimator."""

    name = "haversine"

    def __init__(
        self,
        *,
        average_speed_kmh: float = 50.0,
        road_factor: float = 1.3,
        is_fallback: bool = False,
    ) -> None:
        self._speed_mps = max(average_speed_kmh, 1.0) * 1000.0 / 3600.0
        self._road_factor = max(road_factor, 1.0)
        self._is_fallback = is_fallback

    def _distance(self, origin: GeoPoint, destination: GeoPoint) -> float:
        return haversine_meters(origin, destination) * self._road_factor

    def _duration(self, distance_meters: float) -> float:
        return distance_meters / self._speed_mps

    async def build_route(
        self,
        origin: GeoPoint,
        destination: GeoPoint,
        *,
        profile: TravelProfile = TravelProfile.DRIVING,
        alternatives: bool = False,
    ) -> Route:
        distance = self._distance(origin, destination)
        duration = self._duration(distance)
        geometry = [
            RoutePoint(origin.latitude, origin.longitude, "origin", is_waypoint=True),
            RoutePoint(
                destination.latitude, destination.longitude,
                "destination", is_waypoint=True,
            ),
        ]
        segment = RouteSegment(
            start=origin, end=destination,
            distance_meters=distance, duration_seconds=duration,
            geometry=geometry,
        )
        return Route(
            origin=origin, destination=destination,
            distance_meters=distance, duration_seconds=duration,
            provider=self.name, profile=profile,
            segments=[segment], geometry=geometry,
            is_fallback=self._is_fallback,
        )

    async def calculate_eta(
        self,
        origin: GeoPoint,
        destination: GeoPoint,
        *,
        profile: TravelProfile = TravelProfile.DRIVING,
    ) -> ETAResult:
        distance = self._distance(origin, destination)
        return ETAResult(
            origin=origin, destination=destination,
            eta_seconds=self._duration(distance), distance_meters=distance,
            provider=self.name, is_fallback=self._is_fallback,
        )

    async def calculate_distance(
        self,
        origin: GeoPoint,
        destination: GeoPoint,
        *,
        profile: TravelProfile = TravelProfile.DRIVING,
    ) -> DistanceResult:
        return DistanceResult(
            origin=origin, destination=destination,
            distance_meters=self._distance(origin, destination),
            provider=self.name, is_fallback=self._is_fallback,
        )

    async def snap_to_road(self, point: GeoPoint) -> RoutePoint:
        # No road network: the point is returned unchanged.
        return RoutePoint(point.latitude, point.longitude)

    async def health_check(self) -> ProviderHealth:
        # Always available — it is pure computation.
        return ProviderHealth(provider=self.name, healthy=True, detail="in-process")
