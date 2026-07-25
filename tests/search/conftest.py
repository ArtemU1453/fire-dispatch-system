"""Fixtures for search tests.

The engine's value is its real SQL against PostGIS, so the behavioural tests need
a live PostgreSQL + PostGIS database. They **skip** automatically when none is
reachable (keeping the wider suite hermetic). Each test gets its own NullPool
engine (isolating asyncpg from pytest's per-test event loops) and seeds a small,
self-cleaning fixture dataset.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from geoalchemy2 import WKTElement
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import get_settings
from app.database import get_db_session
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
class SeedData:
    vehicle_type_id: UUID
    hydrant_type_id: UUID
    organization_id: UUID
    status_id: UUID
    capability_id: UUID
    near_id: UUID   # ~300 m from the reference point (Kremlin)
    mid_id: UUID    # ~900 m
    far_id: UUID    # Saint Petersburg (~630 km)


REF_LAT, REF_LON = 55.7539, 37.6208


async def _reachable(engine) -> bool:
    try:
        async with engine.connect() as conn:
            await conn.exec_driver_sql("SELECT 1")
        return True
    except Exception:
        return False


@pytest_asyncio.fixture
async def pg_factory() -> AsyncGenerator[async_sessionmaker]:
    engine = create_async_engine(
        get_settings().SQLALCHEMY_DATABASE_URI, poolclass=NullPool
    )
    if not await _reachable(engine):
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
async def seed(pg_factory: async_sessionmaker) -> SeedData:
    async with pg_factory() as s:
        vt = ResourceType(
            code=f"VEH-{uuid4().hex[:6]}", name="Автоцистерна",
            category=ResourceCategory.VEHICLE,
        )
        ht = ResourceType(
            code=f"HYD-{uuid4().hex[:6]}", name="Гидрант",
            category=ResourceCategory.INFRASTRUCTURE,
        )
        org = Organization(code=f"ORG-{uuid4().hex[:6]}", name="ПЧ-1")
        status = AvailabilityStatus(
            code=f"AV-{uuid4().hex[:6]}", name="Свободен",
            is_available_for_dispatch=True, is_operational=True, sort_order=1,
        )
        cap = Capability(code=f"cap-{uuid4().hex[:6]}", name="fire suppression")
        s.add_all([vt, ht, org, status, cap])
        await s.flush()

        def _res(code, lat, lon, type_id):
            return Resource(
                code=f"{code}-{uuid4().hex[:4]}", name=code,
                resource_type_id=type_id, organization_id=org.id,
                availability_status_id=status.id, latitude=lat, longitude=lon,
                geom=WKTElement(f"POINT({lon} {lat})", srid=4326),
            )

        near = _res("NEAR", 55.7520, 37.6175, vt.id)
        mid = _res("MID", 55.7600, 37.6300, vt.id)
        far = _res("FAR", 59.9343, 30.3351, vt.id)
        hydrant = _res("HYDRANT", 55.7521, 37.6176, ht.id)
        s.add_all([near, mid, far, hydrant])
        await s.flush()
        s.add(ResourceCapability(resource_id=near.id, capability_id=cap.id))
        await s.commit()

        return SeedData(
            vehicle_type_id=vt.id, hydrant_type_id=ht.id, organization_id=org.id,
            status_id=status.id, capability_id=cap.id,
            near_id=near.id, mid_id=mid.id, far_id=far.id,
        )


@pytest_asyncio.fixture
async def session(pg_factory: async_sessionmaker) -> AsyncGenerator[AsyncSession]:
    async with pg_factory() as s:
        yield s


@pytest_asyncio.fixture
async def api_client(
    pg_factory: async_sessionmaker, seed: SeedData
) -> AsyncGenerator[AsyncClient]:
    app = create_app()
    app.state.geo_provider = FakeGeoProvider()
    app.state.geo_cache = InMemoryGeoCache()
    app.state.search_cache = create_search_cache()

    async def _override() -> AsyncGenerator[AsyncSession]:
        async with pg_factory() as s:
            yield s

    app.dependency_overrides[get_db_session] = _override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        yield c
    app.dependency_overrides.clear()
