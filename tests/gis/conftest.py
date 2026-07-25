"""Fixtures for the GIS test suite (hermetic — no network, no PostgreSQL).

Uses the :class:`FakeGeoProvider` and in-memory cache so geocoding flows run
offline, and an in-memory SQLite session factory for the geocoding log so
logging is asserted without a database server.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.gis.cache import InMemoryGeoCache
from app.gis.models import GeocodingLog
from app.gis.providers import FakeGeoProvider
from app.gis.services.geocoding import GeocodingService
from app.main import create_app


@pytest_asyncio.fixture
async def log_session_factory() -> AsyncGenerator[async_sessionmaker]:
    """A SQLite-backed session factory with just the geocoding-log table."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(GeocodingLog.__table__.create)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest_asyncio.fixture
async def geocoding_service(
    log_session_factory: async_sessionmaker,
) -> GeocodingService:
    return GeocodingService(
        provider=FakeGeoProvider(),
        cache=InMemoryGeoCache(),
        log_session_factory=log_session_factory,
    )


@pytest_asyncio.fixture
async def gis_client() -> AsyncGenerator[AsyncClient]:
    """ASGI client with the fake provider + in-memory cache on app state."""
    app = create_app()
    app.state.geo_provider = FakeGeoProvider()
    app.state.geo_cache = InMemoryGeoCache()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
