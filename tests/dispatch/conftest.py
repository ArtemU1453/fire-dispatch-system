"""Fixtures for dispatch integration tests (skip if no PostgreSQL/PostGIS)."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import dataclass
from uuid import uuid4

import pytest
import pytest_asyncio
from geoalchemy2 import WKTElement
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import get_settings
from app.database import get_db_session
from app.dispatch.rules import RuleEngine
from app.gis.cache import InMemoryGeoCache
from app.gis.providers import FakeGeoProvider
from app.main import create_app
from app.models import (
    AvailabilityStatus,
    Capability,
    Organization,
    Resource,
    ResourceCapability,
    ResourceType,
)
from app.models.enums import ResourceCategory
from app.search.cache import create_search_cache


@dataclass
class DispatchSeed:
    organization_id: str


REF_LAT, REF_LON = 55.7539, 37.6208


@pytest_asyncio.fixture
async def pg_factory() -> AsyncGenerator[async_sessionmaker]:
    engine = create_async_engine(
        get_settings().SQLALCHEMY_DATABASE_URI, poolclass=NullPool
    )
    try:
        async with engine.connect() as conn:
            await conn.exec_driver_sql("SELECT 1")
    except Exception:
        await engine.dispose()
        pytest.skip("PostgreSQL not available")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    async with factory() as s:
        for table in (
            "resource_capabilities",
            "resources",
            "capabilities",
            "availability_statuses",
            "resource_types",
            "organizations",
        ):
            await s.execute(text(f"DELETE FROM {table}"))
        await s.commit()
    await engine.dispose()


@pytest_asyncio.fixture
async def seed(pg_factory: async_sessionmaker) -> DispatchSeed:
    async with pg_factory() as s:
        vt = ResourceType(
            code=f"V-{uuid4().hex[:6]}", name="АЦ", category=ResourceCategory.VEHICLE
        )
        org = Organization(code=f"O-{uuid4().hex[:6]}", name="ПЧ-1")
        available = AvailabilityStatus(
            code=f"AVAIL-{uuid4().hex[:4]}", name="Свободен",
            is_available_for_dispatch=True, is_operational=True, sort_order=1,
        )
        busy = AvailabilityStatus(
            code="busy", name="Занят",
            is_available_for_dispatch=False, is_operational=True, sort_order=5,
        )
        fs = Capability(code="fire_suppression", name="Пожаротушение")
        ws = Capability(code="water_supply", name="Водоснабжение")
        s.add_all([vt, org, available, busy, fs, ws])
        await s.flush()

        async def mk(code, lat, lon, status_id, caps):
            r = Resource(
                code=f"{code}-{uuid4().hex[:4]}", name=code,
                resource_type_id=vt.id, organization_id=org.id,
                availability_status_id=status_id, latitude=lat, longitude=lon,
                geom=WKTElement(f"POINT({lon} {lat})", srid=4326),
            )
            s.add(r)
            await s.flush()
            for cid, qty in caps:
                s.add(
                    ResourceCapability(
                        resource_id=r.id, capability_id=cid, quantity=qty
                    )
                )

        await mk("NEAR", 55.7520, 37.6175, available.id, [(fs.id, 1), (ws.id, 1)])
        await mk("MID", 55.7600, 37.6300, available.id, [(fs.id, 1)])
        await mk("BUSY", 55.7521, 37.6176, busy.id, [(fs.id, 1), (ws.id, 1)])
        await mk("FAR", 59.9343, 30.3351, available.id, [(fs.id, 2), (ws.id, 2)])
        await s.commit()
        return DispatchSeed(organization_id=str(org.id))


@pytest_asyncio.fixture
async def api_client(
    pg_factory: async_sessionmaker, seed: DispatchSeed
) -> AsyncGenerator[AsyncClient]:
    app = create_app()
    app.state.geo_provider = FakeGeoProvider()
    app.state.geo_cache = InMemoryGeoCache()
    app.state.search_cache = create_search_cache()
    app.state.rule_engine = RuleEngine()

    async def _override():
        async with pg_factory() as s:
            yield s

    app.dependency_overrides[get_db_session] = _override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        yield c
    app.dependency_overrides.clear()
