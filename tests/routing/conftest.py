"""Fixtures for routing tests (no database, no network required)."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.routing.providers import HaversineRoutingProvider
from app.routing.repositories import InMemoryRouteCache

# Moscow reference points (~3.9 km straight line apart).
ORIGIN = (55.7539, 37.6208)
DEST = (55.7887, 37.6009)


@pytest_asyncio.fixture
async def api_client() -> AsyncGenerator[AsyncClient]:
    """An HTTP client with the routing provider/cache injected on app.state."""
    app = create_app()
    app.state.route_provider = HaversineRoutingProvider(
        average_speed_kmh=50.0, road_factor=1.3
    )
    app.state.route_cache = InMemoryRouteCache(default_ttl=60, max_entries=100)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
