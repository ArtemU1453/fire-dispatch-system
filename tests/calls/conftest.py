"""Fixtures for call-management integration tests (skip if no PostgreSQL).

Seeds an incident type and one existing incident (so both the create-incident and
link-existing paths can be exercised), then cleans up its own rows. The call
tables are exclusively this module's, so cleanup removes all call rows.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import dataclass
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import get_settings
from app.database import get_db_session
from app.incidents.models.entities import Incident
from app.incidents.models.enums import (
    IncidentCategory,
    IncidentPriority,
    IncidentSource,
    IncidentStatus,
)
from app.main import create_app
from app.models import IncidentType

PREFIX = f"C{uuid4().hex[:8]}"


@dataclass
class CallSeed:
    prefix: str
    incident_type_id: str
    incident_id: str


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
    await _cleanup(factory)
    await engine.dispose()


async def _cleanup(factory: async_sessionmaker) -> None:
    p = f"{PREFIX}%"
    async with factory() as s:
        # calls own their child tables (CASCADE); this module owns them all.
        await s.execute(text("DELETE FROM calls"))
        await s.execute(
            text(
                "DELETE FROM incidents WHERE incident_type_id IN "
                "(SELECT id FROM incident_types WHERE code LIKE :p)"
            ),
            {"p": p},
        )
        await s.execute(
            text("DELETE FROM incident_types WHERE code LIKE :p"), {"p": p}
        )
        await s.commit()


@pytest_asyncio.fixture
async def seed(pg_factory: async_sessionmaker) -> CallSeed:
    async with pg_factory() as s:
        itype = IncidentType(code=f"{PREFIX}-FIRE", name="Пожар")
        s.add(itype)
        await s.flush()
        incident = Incident(
            number=f"{PREFIX}-INC",
            incident_type_id=itype.id,
            category=IncidentCategory.FIRE,
            source=IncidentSource.PHONE,
            status=IncidentStatus.CREATED,
            priority=IncidentPriority.NORMAL,
            title="Существующее происшествие",
        )
        s.add(incident)
        await s.flush()
        result = CallSeed(
            prefix=PREFIX,
            incident_type_id=str(itype.id),
            incident_id=str(incident.id),
        )
        await s.commit()
        return result


@pytest_asyncio.fixture
async def api_client(
    pg_factory: async_sessionmaker, seed: CallSeed
) -> AsyncGenerator[AsyncClient]:
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
