"""RouteService — build routes, distances and geometry via a RoutingProvider.

Coordinates the provider and the route-reuse cache, records structured logs
(provider, response time, distance, ETA, errors) and turns provider failures into
clear, catchable errors — the caller (or the Dispatch Engine, via ETAService)
never crashes because a routing backend is down.
"""

from __future__ import annotations

import time

from app.core.logging import get_logger
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
    RoutePoint,
    RoutingResponse,
    TravelProfile,
)
from app.routing.repositories.route_cache import (
    NullRouteCache,
    RouteCache,
    route_cache_key,
)

logger = get_logger(__name__)


class RouteService:
    """Business logic over a routing provider (build / distance / geometry)."""

    def __init__(
        self, provider: RoutingProvider, *, cache: RouteCache | None = None
    ) -> None:
        self._provider = provider
        self._cache = cache or NullRouteCache()

    async def build_route(
        self,
        origin: GeoPoint,
        destination: GeoPoint,
        *,
        profile: TravelProfile = TravelProfile.DRIVING,
        alternatives: bool = False,
        use_cache: bool = True,
    ) -> RoutingResponse:
        key = route_cache_key(origin, destination, profile)
        if use_cache and not alternatives:
            cached = await self._cache.get(key)
            if cached is not None:
                logger.info("routing: cache hit (%s) key=%s", cached.provider, key)
                return RoutingResponse(
                    route=cached, provider=cached.provider,
                    response_time_ms=0.0, is_fallback=cached.is_fallback,
                )

        started = time.perf_counter()
        route = await self._call(
            "build_route",
            lambda: self._provider.build_route(
                origin, destination, profile=profile, alternatives=alternatives
            ),
        )
        elapsed_ms = round((time.perf_counter() - started) * 1000.0, 1)
        logger.info(
            "routing: build_route provider=%s distance=%.0fm eta=%.0fs "
            "time=%.1fms fallback=%s",
            route.provider, route.distance_meters, route.duration_seconds,
            elapsed_ms, route.is_fallback,
        )
        if use_cache and not alternatives:
            await self._cache.set(key, route)
        return RoutingResponse(
            route=route, provider=route.provider,
            response_time_ms=elapsed_ms, is_fallback=route.is_fallback,
        )

    async def calculate_distance(
        self,
        origin: GeoPoint,
        destination: GeoPoint,
        *,
        profile: TravelProfile = TravelProfile.DRIVING,
    ) -> DistanceResult:
        result = await self._call(
            "calculate_distance",
            lambda: self._provider.calculate_distance(
                origin, destination, profile=profile
            ),
        )
        logger.info(
            "routing: distance provider=%s distance=%.0fm fallback=%s",
            result.provider, result.distance_meters, result.is_fallback,
        )
        return result

    async def calculate_eta(
        self,
        origin: GeoPoint,
        destination: GeoPoint,
        *,
        profile: TravelProfile = TravelProfile.DRIVING,
    ) -> ETAResult:
        result = await self._call(
            "calculate_eta",
            lambda: self._provider.calculate_eta(origin, destination, profile=profile),
        )
        logger.info(
            "routing: eta provider=%s eta=%.0fs distance=%.0fm fallback=%s",
            result.provider, result.eta_seconds, result.distance_meters,
            result.is_fallback,
        )
        return result

    async def get_geometry(
        self,
        origin: GeoPoint,
        destination: GeoPoint,
        *,
        profile: TravelProfile = TravelProfile.DRIVING,
    ) -> list[RoutePoint]:
        response = await self.build_route(origin, destination, profile=profile)
        return response.route.geometry

    async def get_waypoints(
        self,
        origin: GeoPoint,
        destination: GeoPoint,
        *,
        profile: TravelProfile = TravelProfile.DRIVING,
    ) -> list[RoutePoint]:
        response = await self.build_route(origin, destination, profile=profile)
        return response.route.waypoints

    async def snap_to_road(self, point: GeoPoint) -> RoutePoint:
        return await self._call(
            "snap_to_road", lambda: self._provider.snap_to_road(point)
        )

    async def health(self) -> ProviderHealth:
        try:
            return await self._provider.health_check()
        except RoutingError as exc:
            logger.warning("routing: health_check error: %s", exc)
            return ProviderHealth(
                provider=self._provider.name, healthy=False, detail=str(exc)
            )

    async def _call(self, op: str, func):
        try:
            return await func()
        except ProviderUnavailableError as exc:
            logger.error("routing: %s provider unavailable: %s", op, exc)
            raise
        except RoutingError as exc:
            logger.warning("routing: %s failed: %s", op, exc)
            raise


__all__ = ["RouteService"]
