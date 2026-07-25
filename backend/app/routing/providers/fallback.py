"""Fallback routing provider — a resilient chain of backends.

Wraps an ordered list of providers. Each operation tries them in order; when a
provider is **unavailable** (``ProviderUnavailableError``) the next one is used,
so a routing backend going down never fails the whole operation (or the Dispatch
Engine). A result served by a non-primary provider is flagged ``is_fallback``.

Genuine routing answers such as "no route exists" (``RoutingError``) are **not**
masked by falling back — only unavailability is.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import TypeVar

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
    Route,
    RoutePoint,
    TravelProfile,
)

logger = get_logger(__name__)

_T = TypeVar("_T")


class FallbackRoutingProvider(RoutingProvider):
    """Tries providers in order, falling back on unavailability."""

    def __init__(self, providers: Sequence[RoutingProvider]) -> None:
        if not providers:
            raise ValueError("FallbackRoutingProvider needs at least one provider")
        self._providers = list(providers)
        self.name = "fallback[" + ">".join(p.name for p in self._providers) + "]"

    async def _run(
        self, op: Callable[[RoutingProvider], Awaitable[_T]], mark
    ) -> _T:
        last: ProviderUnavailableError | None = None
        for index, provider in enumerate(self._providers):
            try:
                result = await op(provider)
            except ProviderUnavailableError as exc:
                last = exc
                logger.warning(
                    "Routing provider %s unavailable, falling back: %s",
                    provider.name, exc,
                )
                continue
            if index > 0:
                mark(result)
            return result
        raise last or ProviderUnavailableError("No routing provider available")

    async def build_route(
        self,
        origin: GeoPoint,
        destination: GeoPoint,
        *,
        profile: TravelProfile = TravelProfile.DRIVING,
        alternatives: bool = False,
    ) -> Route:
        def mark(r: Route) -> None:
            r.is_fallback = True

        return await self._run(
            lambda p: p.build_route(
                origin, destination, profile=profile, alternatives=alternatives
            ),
            mark,
        )

    async def calculate_eta(
        self,
        origin: GeoPoint,
        destination: GeoPoint,
        *,
        profile: TravelProfile = TravelProfile.DRIVING,
    ) -> ETAResult:
        def mark(r: ETAResult) -> None:
            r.is_fallback = True

        return await self._run(
            lambda p: p.calculate_eta(origin, destination, profile=profile), mark
        )

    async def calculate_distance(
        self,
        origin: GeoPoint,
        destination: GeoPoint,
        *,
        profile: TravelProfile = TravelProfile.DRIVING,
    ) -> DistanceResult:
        def mark(r: DistanceResult) -> None:
            r.is_fallback = True

        return await self._run(
            lambda p: p.calculate_distance(origin, destination, profile=profile), mark
        )

    async def snap_to_road(self, point: GeoPoint) -> RoutePoint:
        return await self._run(lambda p: p.snap_to_road(point), lambda _r: None)

    async def health_check(self) -> ProviderHealth:
        details: list[str] = []
        any_healthy = False
        for provider in self._providers:
            try:
                health = await provider.health_check()
            except RoutingError as exc:
                details.append(f"{provider.name}: error ({exc})")
                continue
            any_healthy = any_healthy or health.healthy
            details.append(f"{provider.name}: {'up' if health.healthy else 'down'}")
        return ProviderHealth(
            provider=self.name, healthy=any_healthy, detail="; ".join(details)
        )

    async def aclose(self) -> None:
        for provider in self._providers:
            await provider.aclose()
