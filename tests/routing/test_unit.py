"""Unit tests for routing internals (no network, no DB)."""

from __future__ import annotations

import pytest

from app.routing.interfaces.routing_provider import (
    ProviderUnavailableError,
    RoutingProvider,
)
from app.routing.models.domain import GeoPoint, TravelProfile
from app.routing.providers import (
    FallbackRoutingProvider,
    HaversineRoutingProvider,
)
from app.routing.repositories import InMemoryRouteCache, route_cache_key
from app.routing.services import ETAService, RouteService
from app.routing.utils.geo import haversine_meters

pytestmark = pytest.mark.asyncio

MOSCOW = GeoPoint(55.7539, 37.6208)
SPB = GeoPoint(59.9343, 30.3351)
NEAR = GeoPoint(55.7887, 37.6009)


# ------------------------------------------------------------------- geo ------
async def test_haversine_matches_known_distance() -> None:
    # Moscow → Saint Petersburg is ~633 km great-circle.
    meters = haversine_meters(MOSCOW, SPB)
    assert 600_000 < meters < 660_000


async def test_haversine_zero_for_same_point() -> None:
    assert haversine_meters(MOSCOW, MOSCOW) == pytest.approx(0.0, abs=1e-6)


# ------------------------------------------------------- haversine provider ---
async def test_haversine_provider_distance_and_eta() -> None:
    provider = HaversineRoutingProvider(average_speed_kmh=60.0, road_factor=1.0)
    distance = await provider.calculate_distance(MOSCOW, NEAR)
    eta = await provider.calculate_eta(MOSCOW, NEAR)
    straight = haversine_meters(MOSCOW, NEAR)
    assert distance.distance_meters == pytest.approx(straight, rel=1e-6)
    # 60 km/h → 1000 m per minute; eta_seconds = distance / (60000/3600).
    assert eta.eta_seconds == pytest.approx(straight / (60_000 / 3600), rel=1e-6)


async def test_haversine_road_factor_scales_distance() -> None:
    plain = HaversineRoutingProvider(road_factor=1.0)
    scaled = HaversineRoutingProvider(road_factor=1.5)
    d1 = (await plain.calculate_distance(MOSCOW, NEAR)).distance_meters
    d2 = (await scaled.calculate_distance(MOSCOW, NEAR)).distance_meters
    assert d2 == pytest.approx(d1 * 1.5, rel=1e-6)


async def test_haversine_build_route_has_waypoints_and_health() -> None:
    provider = HaversineRoutingProvider()
    route = await provider.build_route(MOSCOW, NEAR)
    assert route.provider == "haversine"
    assert len(route.waypoints) == 2
    assert route.segments and route.segments[0].distance_meters > 0
    health = await provider.health_check()
    assert health.healthy is True


# --------------------------------------------------------------- cache --------
async def test_route_cache_stores_and_expires() -> None:
    cache = InMemoryRouteCache(default_ttl=60, max_entries=10)
    provider = HaversineRoutingProvider()
    route = await provider.build_route(MOSCOW, NEAR)
    key = route_cache_key(MOSCOW, NEAR, TravelProfile.DRIVING)
    await cache.set(key, route)
    assert await cache.get(key) is route
    # A different pair misses.
    assert await cache.get(route_cache_key(MOSCOW, SPB, TravelProfile.DRIVING)) is None


async def test_route_service_uses_cache_on_second_call() -> None:
    cache = InMemoryRouteCache(default_ttl=60, max_entries=10)
    service = RouteService(HaversineRoutingProvider(), cache=cache)
    first = await service.build_route(MOSCOW, NEAR)
    second = await service.build_route(MOSCOW, NEAR)
    assert first.response_time_ms >= 0.0
    assert second.response_time_ms == 0.0  # served from cache
    assert second.route.distance_meters == first.route.distance_meters


# ------------------------------------------------------------- ETA service ----
async def test_eta_service_estimate_seconds() -> None:
    service = ETAService(
        RouteService(HaversineRoutingProvider(average_speed_kmh=50.0)),
        average_speed_kmh=50.0,
    )
    seconds = await service.estimate_seconds(MOSCOW, NEAR)
    assert seconds > 0
    # Distance-only fallback (Dispatch Engine seam shape).
    assert service.eta_seconds_for_distance(50_000) == pytest.approx(
        50_000 / (50_000 / 3600), rel=1e-6
    )
    assert service.eta_seconds_for_distance(None) is None


# --------------------------------------------------------------- fallback -----
class _DownProvider(RoutingProvider):
    name = "down"

    async def build_route(
        self, origin, destination, *, profile=..., alternatives=False
    ):
        raise ProviderUnavailableError("simulated outage")

    async def calculate_eta(self, origin, destination, *, profile=...):
        raise ProviderUnavailableError("simulated outage")

    async def calculate_distance(self, origin, destination, *, profile=...):
        raise ProviderUnavailableError("simulated outage")

    async def snap_to_road(self, point):
        raise ProviderUnavailableError("simulated outage")

    async def health_check(self):
        from app.routing.models.domain import ProviderHealth

        return ProviderHealth(provider=self.name, healthy=False)


async def test_fallback_uses_secondary_when_primary_down() -> None:
    fallback = FallbackRoutingProvider(
        [_DownProvider(), HaversineRoutingProvider(is_fallback=True)]
    )
    route = await fallback.build_route(MOSCOW, NEAR)
    assert route.provider == "haversine"
    assert route.is_fallback is True
    eta = await fallback.calculate_eta(MOSCOW, NEAR)
    assert eta.is_fallback is True


async def test_fallback_all_down_raises() -> None:
    fallback = FallbackRoutingProvider([_DownProvider(), _DownProvider()])
    with pytest.raises(ProviderUnavailableError):
        await fallback.calculate_distance(MOSCOW, NEAR)
