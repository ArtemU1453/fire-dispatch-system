"""ETAService — the single entry point for estimated time of arrival.

Responsible **only** for ETA. This is the service the Dispatch Engine will use to
obtain arrival times (via its ``ETAProvider`` seam) — it depends on the routing
provider through :class:`RouteService`, never on a concrete backend. Kept separate
from :class:`RouteService` so ETA can evolve (or be cached / batched) independently
of full route building.

Note: this stage does not modify the Dispatch Engine. A thin adapter implementing
the Dispatch Engine's ``ETAProvider`` interface can delegate to this service
without any change here.
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.routing.models.domain import ETAResult, GeoPoint, TravelProfile
from app.routing.services.route_service import RouteService

logger = get_logger(__name__)


class ETAService:
    """Computes ETA between points (delegating to the routing provider)."""

    def __init__(
        self, route_service: RouteService, *, average_speed_kmh: float = 50.0
    ) -> None:
        self._routes = route_service
        self._speed_mps = max(average_speed_kmh, 1.0) * 1000.0 / 3600.0

    async def estimate(
        self,
        origin: GeoPoint,
        destination: GeoPoint,
        *,
        profile: TravelProfile = TravelProfile.DRIVING,
    ) -> ETAResult:
        """The ETA between two points."""
        return await self._routes.calculate_eta(origin, destination, profile=profile)

    async def estimate_seconds(
        self,
        origin: GeoPoint,
        destination: GeoPoint,
        *,
        profile: TravelProfile = TravelProfile.DRIVING,
    ) -> float:
        """ETA in seconds (the value the Dispatch Engine's seam consumes)."""
        result = await self.estimate(origin, destination, profile=profile)
        return result.eta_seconds

    def eta_seconds_for_distance(self, distance_meters: float | None) -> float | None:
        """Distance-only ETA fallback (no origin/destination available).

        Matches the shape of the Dispatch Engine's ``ETAProvider.estimate`` seam:
        given a straight-line/route distance it returns an ETA in seconds using
        the configured average speed. Returns ``None`` when distance is unknown.
        """
        if distance_meters is None:
            return None
        return distance_meters / self._speed_mps


__all__ = ["ETAService"]
