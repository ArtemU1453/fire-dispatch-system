"""OSRM routing provider (HTTP).

Talks to an OSRM server (``/route``, ``/nearest``). It is the concrete "real"
provider for this stage; other backends (GraphHopper, Valhalla, OpenRouteService,
commercial APIs) can be added later behind the same :class:`RoutingProvider`
interface without touching the services.

Network/HTTP failures raise :class:`ProviderUnavailableError` so a fallback
provider can take over; malformed responses raise :class:`RoutingError`.
"""

from __future__ import annotations

import time

import httpx

from app.routing.interfaces.routing_provider import (
    ProviderUnavailableError,
    RoutingError,
    RoutingProvider,
)
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

_PROFILE_PATH = {
    TravelProfile.DRIVING: "driving",
    TravelProfile.WALKING: "walking",
    TravelProfile.CYCLING: "cycling",
}


class OSRMProvider(RoutingProvider):
    """Routing backed by an OSRM HTTP server."""

    name = "osrm"

    def __init__(
        self,
        base_url: str,
        *,
        client: httpx.AsyncClient | None = None,
        timeout: float = 8.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client = client or httpx.AsyncClient(timeout=timeout)
        self._owns_client = client is None

    # ------------------------------------------------------------ requests
    async def _get(self, path: str, params: dict) -> dict:
        url = f"{self._base_url}{path}"
        try:
            response = await self._client.get(url, params=params, timeout=self._timeout)
        except httpx.HTTPError as exc:  # network, timeout, connection
            raise ProviderUnavailableError(f"OSRM unreachable: {exc}") from exc
        if response.status_code >= 500:
            raise ProviderUnavailableError(f"OSRM server error {response.status_code}")
        try:
            payload = response.json()
        except ValueError as exc:
            raise RoutingError("OSRM returned a non-JSON response") from exc
        code = payload.get("code")
        if code != "Ok":
            # NoRoute / NoSegment / InvalidQuery etc.
            raise RoutingError(f"OSRM: {code or 'unknown error'}")
        return payload

    def _coords(self, *points: GeoPoint) -> str:
        return ";".join(f"{p.longitude},{p.latitude}" for p in points)

    async def _route_payload(
        self, origin: GeoPoint, destination: GeoPoint, profile: TravelProfile,
        *, overview: str, alternatives: bool,
    ) -> dict:
        mode = _PROFILE_PATH.get(profile, "driving")
        path = f"/route/v1/{mode}/{self._coords(origin, destination)}"
        params = {
            "overview": overview,
            "geometries": "geojson",
            "alternatives": "true" if alternatives else "false",
            "steps": "false",
        }
        payload = await self._get(path, params)
        routes = payload.get("routes") or []
        if not routes:
            raise RoutingError("OSRM returned no route")
        return routes[0]

    # ------------------------------------------------------------ interface
    async def build_route(
        self,
        origin: GeoPoint,
        destination: GeoPoint,
        *,
        profile: TravelProfile = TravelProfile.DRIVING,
        alternatives: bool = False,
    ) -> Route:
        route = await self._route_payload(
            origin, destination, profile, overview="full", alternatives=alternatives
        )
        geometry = [
            RoutePoint(latitude=lat, longitude=lon)
            for lon, lat in route.get("geometry", {}).get("coordinates", [])
        ]
        if geometry:
            geometry[0] = RoutePoint(
                geometry[0].latitude, geometry[0].longitude, "origin", is_waypoint=True
            )
            geometry[-1] = RoutePoint(
                geometry[-1].latitude, geometry[-1].longitude,
                "destination", is_waypoint=True,
            )
        segments = [
            RouteSegment(
                start=origin, end=destination,
                distance_meters=float(leg.get("distance", 0.0)),
                duration_seconds=float(leg.get("duration", 0.0)),
            )
            for leg in route.get("legs", [])
        ]
        return Route(
            origin=origin, destination=destination,
            distance_meters=float(route.get("distance", 0.0)),
            duration_seconds=float(route.get("duration", 0.0)),
            provider=self.name, profile=profile,
            segments=segments, geometry=geometry,
        )

    async def calculate_eta(
        self,
        origin: GeoPoint,
        destination: GeoPoint,
        *,
        profile: TravelProfile = TravelProfile.DRIVING,
    ) -> ETAResult:
        route = await self._route_payload(
            origin, destination, profile, overview="false", alternatives=False
        )
        return ETAResult(
            origin=origin, destination=destination,
            eta_seconds=float(route.get("duration", 0.0)),
            distance_meters=float(route.get("distance", 0.0)),
            provider=self.name,
        )

    async def calculate_distance(
        self,
        origin: GeoPoint,
        destination: GeoPoint,
        *,
        profile: TravelProfile = TravelProfile.DRIVING,
    ) -> DistanceResult:
        route = await self._route_payload(
            origin, destination, profile, overview="false", alternatives=False
        )
        return DistanceResult(
            origin=origin, destination=destination,
            distance_meters=float(route.get("distance", 0.0)),
            provider=self.name,
        )

    async def snap_to_road(self, point: GeoPoint) -> RoutePoint:
        path = f"/nearest/v1/driving/{self._coords(point)}"
        payload = await self._get(path, {"number": "1"})
        waypoints = payload.get("waypoints") or []
        if not waypoints:
            raise RoutingError("OSRM returned no snap candidate")
        lon, lat = waypoints[0]["location"]
        return RoutePoint(latitude=lat, longitude=lon, name=waypoints[0].get("name"))

    async def health_check(self) -> ProviderHealth:
        started = time.perf_counter()
        try:
            await self._get(
                f"/nearest/v1/driving/{self._coords(GeoPoint(55.75, 37.62))}",
                {"number": "1"},
            )
        except RoutingError as exc:
            return ProviderHealth(provider=self.name, healthy=False, detail=str(exc))
        latency = (time.perf_counter() - started) * 1000.0
        return ProviderHealth(
            provider=self.name, healthy=True, detail="ok", latency_ms=round(latency, 1)
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()
