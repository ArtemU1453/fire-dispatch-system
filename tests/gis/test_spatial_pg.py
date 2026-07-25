"""PostGIS spatial tests.

These require a real PostgreSQL + PostGIS database (they exercise ST_* functions
that SQLite cannot run). The whole module is skipped when the configured database
is unreachable, so the rest of the suite stays hermetic.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from geoalchemy2 import WKTElement
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import get_settings
from app.gis.repositories.spatial import SpatialRepository
from app.models import Organization, Resource, ResourceType
from app.models.enums import ResourceCategory

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def pg_session() -> AsyncGenerator[AsyncSession]:
    # A dedicated engine per test avoids reusing asyncpg connections across
    # pytest's per-test event loops. NullPool ensures nothing is pooled.
    engine = create_async_engine(
        get_settings().SQLALCHEMY_DATABASE_URI, poolclass=NullPool
    )
    try:
        async with engine.connect() as conn:
            await conn.exec_driver_sql("SELECT 1")
    except Exception:
        await engine.dispose()
        pytest.skip("PostgreSQL not available")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
    await engine.dispose()


async def _seed_resource(
    session: AsyncSession, code: str, lat: float, lon: float
) -> None:
    rt = ResourceType(code=f"RT-{code}", name="t", category=ResourceCategory.VEHICLE)
    org = Organization(code=f"ORG-{code}", name="o")
    session.add_all([rt, org])
    await session.flush()
    session.add(
        Resource(
            code=code,
            name=code,
            resource_type_id=rt.id,
            organization_id=org.id,
            latitude=lat,
            longitude=lon,
            geom=WKTElement(f"POINT({lon} {lat})", srid=4326),
        )
    )
    await session.flush()


async def test_distance_meters(pg_session: AsyncSession) -> None:
    repo = SpatialRepository(pg_session)
    # Moscow → Saint Petersburg is roughly 630–640 km.
    meters = await repo.distance_meters(55.7558, 37.6173, 59.9343, 30.3351)
    assert 600_000 < meters < 700_000


async def test_within_radius_finds_near_and_excludes_far(
    pg_session: AsyncSession,
) -> None:
    await _seed_resource(pg_session, "NEAR", 55.7560, 37.6175)
    await _seed_resource(pg_session, "FAR", 59.9343, 30.3351)
    repo = SpatialRepository(pg_session)
    rows = await repo.within_radius(55.7558, 37.6173, radius_meters=2000)
    codes = {r.code for r in rows}
    assert "NEAR" in codes
    assert "FAR" not in codes


async def test_within_bbox(pg_session: AsyncSession) -> None:
    await _seed_resource(pg_session, "INBOX", 55.75, 37.62)
    repo = SpatialRepository(pg_session)
    rows = await repo.within_bbox(37.5, 55.7, 37.7, 55.8)
    assert any(r.code == "INBOX" for r in rows)


async def test_within_polygon(pg_session: AsyncSession) -> None:
    await _seed_resource(pg_session, "INPOLY", 55.75, 37.62)
    repo = SpatialRepository(pg_session)
    wkt = "POLYGON((37.5 55.7, 37.7 55.7, 37.7 55.8, 37.5 55.8, 37.5 55.7))"
    rows = await repo.within_polygon(wkt)
    assert any(r.code == "INPOLY" for r in rows)
