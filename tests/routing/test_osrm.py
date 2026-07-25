"""OSRM provider tests using a mocked HTTP transport (no real server)."""

from __future__ import annotations

import httpx
import pytest

from app.routing.interfaces.routing_provider import (
    ProviderUnavailableError,
    RoutingError,
)
from app.routing.models.domain import GeoPoint
from app.routing.providers import OSRMProvider

pytestmark = pytest.mark.asyncio

A = GeoPoint(55.7539, 37.6208)
B = GeoPoint(55.7887, 37.6009)

_ROUTE_OK = {
    "code": "Ok",
    "routes": [
        {
            "distance": 4200.5,
            "duration": 360.0,
            "geometry": {
                "coordinates": [
                    [37.6208, 55.7539],
                    [37.6100, 55.7700],
                    [37.6009, 55.7887],
                ]
            },
            "legs": [{"distance": 4200.5, "duration": 360.0}],
        }
    ],
}

_NEAREST_OK = {
    "code": "Ok",
    "waypoints": [{"location": [37.6210, 55.7540], "name": "Тверская"}],
}


def _provider(handler) -> OSRMProvider:
    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    return OSRMProvider("http://osrm.local", client=client)


async def test_build_route_parses_osrm_payload() -> None:
    provider = _provider(lambda req: httpx.Response(200, json=_ROUTE_OK))
    route = await provider.build_route(A, B)
    assert route.provider == "osrm"
    assert route.distance_meters == pytest.approx(4200.5)
    assert route.duration_seconds == pytest.approx(360.0)
    assert len(route.geometry) == 3
    assert route.geometry[0].is_waypoint and route.geometry[-1].is_waypoint
    assert route.segments[0].distance_meters == pytest.approx(4200.5)


async def test_eta_and_distance() -> None:
    provider = _provider(lambda req: httpx.Response(200, json=_ROUTE_OK))
    eta = await provider.calculate_eta(A, B)
    dist = await provider.calculate_distance(A, B)
    assert eta.eta_seconds == pytest.approx(360.0)
    assert dist.distance_meters == pytest.approx(4200.5)


async def test_snap_to_road() -> None:
    provider = _provider(lambda req: httpx.Response(200, json=_NEAREST_OK))
    snapped = await provider.snap_to_road(A)
    assert snapped.latitude == pytest.approx(55.7540)
    assert snapped.longitude == pytest.approx(37.6210)
    assert snapped.name == "Тверская"


async def test_server_error_is_provider_unavailable() -> None:
    provider = _provider(lambda req: httpx.Response(502, text="bad gateway"))
    with pytest.raises(ProviderUnavailableError):
        await provider.build_route(A, B)


async def test_network_error_is_provider_unavailable() -> None:
    def boom(req: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no route to host", request=req)

    provider = _provider(boom)
    with pytest.raises(ProviderUnavailableError):
        await provider.calculate_eta(A, B)


async def test_no_route_is_routing_error() -> None:
    provider = _provider(
        lambda req: httpx.Response(200, json={"code": "NoRoute", "routes": []})
    )
    with pytest.raises(RoutingError):
        await provider.build_route(A, B)


async def test_health_check_ok() -> None:
    provider = _provider(lambda req: httpx.Response(200, json=_NEAREST_OK))
    health = await provider.health_check()
    assert health.healthy is True
    assert health.provider == "osrm"
