"""Fixtures for Crisis Management tests.

The API/integration tests need PostgreSQL (the module has its own tables); they
skip when no database is reachable. The crisis schema is self-contained (no FKs
into other modules), so cleanup is a simple prefix delete of ``crisis_*`` rows.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import get_settings
from app.database import get_db_session
from app.main import create_app

# Every operation created by the tests uses this code prefix, so cleanup can
# find and remove exactly the rows the tests inserted.
PREFIX = "CMTEST"


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
        import pytest

        pytest.skip("PostgreSQL not available")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await _cleanup(factory)
    await engine.dispose()


async def _cleanup(factory: async_sessionmaker) -> None:
    async with factory() as s:
        # Deleting operations cascades to all child crisis_* rows (ON DELETE
        # CASCADE); response levels are seeded reference data and left intact.
        await s.execute(
            text("DELETE FROM crisis_operations WHERE code LIKE :p"),
            {"p": f"{PREFIX}%"},
        )
        await s.commit()


@pytest_asyncio.fixture
async def client(pg_factory: async_sessionmaker) -> AsyncGenerator[AsyncClient]:
    app = create_app()

    async def _override():
        async with pg_factory() as s:
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise

    app.dependency_overrides[get_db_session] = _override
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://t"
    ) as c:
        yield c
    app.dependency_overrides.clear()
