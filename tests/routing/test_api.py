"""API tests for the routing endpoints (no DB, no network)."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.routing.interfaces.routing_provider import ProviderUnavailableError
from app.routing.providers import HaversineRoutingProvider
from app.routing.repositories import NullRouteCache

from .conftest import DEST, ORIGIN

pytestmark = pytest.mark.asyncio


async def test_route_endpoint(api_client: AsyncClient) -> None:
    resp = await api_client.get(
        "/api/v1/routing/route",
        params={
            "from_lat": ORIGIN[0], "from_lon": ORIGIN[1],
            "to_lat": DEST[0], "to_lon": DEST[1],
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["provider"] == "haversine"
    assert body["distance_meters"] > 0
    assert body["eta_minutes"] > 0
    assert len(body["waypoints"]) == 2


async def test_eta_endpoint(api_client: AsyncClient) -> None:
    resp = await api_client.post(
        "/api/v1/routing/eta",
        json={
            "origin": {"latitude": ORIGIN[0], "longitude": ORIGIN[1]},
            "destination": {"latitude": DEST[0], "longitude": DEST[1]},
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["eta_seconds"] > 0
    assert body["distance_meters"] > 0


async def test_distance_endpoint(api_client: AsyncClient) -> None:
    resp = await api_client.post(
        "/api/v1/routing/distance",
        json={
            "origin": {"latitude": ORIGIN[0], "longitude": ORIGIN[1]},
            "destination": {"latitude": DEST[0], "longitude": DEST[1]},
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["distance_km"] > 0


async def test_health_endpoint(api_client: AsyncClient) -> None:
    resp = await api_client.get("/api/v1/routing/health")
    assert resp.status_code == 200
    assert resp.json()["healthy"] is True


async def test_invalid_coordinates_rejected(api_client: AsyncClient) -> None:
    resp = await api_client.get(
        "/api/v1/routing/route",
        params={"from_lat": 200, "from_lon": 0, "to_lat": 0, "to_lon": 0},
    )
    assert resp.status_code == 422


class _DownProvider(HaversineRoutingProvider):
    async def build_route(self, *a, **k):
        raise ProviderUnavailableError("outage")


async def test_provider_unavailable_returns_503() -> None:
    app = create_app()
    app.state.route_provider = _DownProvider()
    app.state.route_cache = NullRouteCache()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/routing/route",
            params={
                "from_lat": ORIGIN[0], "from_lon": ORIGIN[1],
                "to_lat": DEST[0], "to_lon": DEST[1],
            },
        )
    assert resp.status_code == 503
