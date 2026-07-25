"""The RoutingProvider abstraction — the single seam to any routing backend.

Every routing backend (OSRM now; GraphHopper, Valhalla, OpenRouteService,
commercial APIs or an in-house router later) implements this interface. Services
depend only on ``RoutingProvider``, never on a concrete backend, so a provider is
swapped purely through configuration (Dependency Inversion). Adding a provider
requires no change to the business logic (RouteService / ETAService).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.routing.models.domain import (
    DistanceResult,
    ETAResult,
    GeoPoint,
    ProviderHealth,
    Route,
    RoutePoint,
    TravelProfile,
)


class RoutingError(RuntimeError):
    """A routing operation failed (bad input, parse error, provider fault)."""


class ProviderUnavailableError(RoutingError):
    """The routing backend is unreachable or unhealthy.

    Raised so callers can fall back to another provider without the whole
    operation (or the Dispatch Engine) failing.
    """


class RoutingProvider(ABC):
    """Abstract routing backend.

    Concrete providers are configured (endpoint, timeout) via the constructor and
    are otherwise stateless with respect to a request.
    """

    #: Stable identifier recorded on results and in the routing log.
    name: str = "base"

    @abstractmethod
    async def build_route(
        self,
        origin: GeoPoint,
        destination: GeoPoint,
        *,
        profile: TravelProfile = TravelProfile.DRIVING,
        alternatives: bool = False,
    ) -> Route:
        """Build a full route (distance, duration, geometry) between two points."""
        raise NotImplementedError

    @abstractmethod
    async def calculate_eta(
        self,
        origin: GeoPoint,
        destination: GeoPoint,
        *,
        profile: TravelProfile = TravelProfile.DRIVING,
    ) -> ETAResult:
        """Estimate travel time (seconds) between two points."""
        raise NotImplementedError

    @abstractmethod
    async def calculate_distance(
        self,
        origin: GeoPoint,
        destination: GeoPoint,
        *,
        profile: TravelProfile = TravelProfile.DRIVING,
    ) -> DistanceResult:
        """Compute travel distance (meters) between two points."""
        raise NotImplementedError

    @abstractmethod
    async def snap_to_road(self, point: GeoPoint) -> RoutePoint:
        """Snap a coordinate to the nearest routable position on the network."""
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> ProviderHealth:
        """Report whether the backend is reachable and usable."""
        raise NotImplementedError

    async def aclose(self) -> None:
        """Release resources (HTTP clients). Default is a no-op."""
        return None
