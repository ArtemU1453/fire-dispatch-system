"""Fixtures for rules integration tests (skip if no PostgreSQL).

Real rule content lives in native PG enums and JSONB, so the integration tests
run against PostgreSQL. When no database is reachable the fixtures skip, keeping
the suite hermetic on machines without one. Each run uses a unique ``code``
prefix and cleans up only its own rows, so tests never clobber shared catalog
data from other stages.
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
from app.main import create_app
from app.models import IncidentType
from app.rules.models import RuleCategory

PREFIX = f"T{uuid4().hex[:8]}"


@dataclass
class RulesSeed:
    category_id: str
    other_category_id: str
    incident_type_id: str
    prefix: str


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
        await s.execute(
            text("DELETE FROM rules WHERE code LIKE :p"), {"p": f"{PREFIX}%"}
        )
        await s.execute(
            text("DELETE FROM rule_categories WHERE code LIKE :p"),
            {"p": f"{PREFIX}%"},
        )
        await s.execute(
            text("DELETE FROM incident_types WHERE code LIKE :p"),
            {"p": f"{PREFIX}%"},
        )
        await s.commit()
    await engine.dispose()


@pytest_asyncio.fixture
async def seed(pg_factory: async_sessionmaker) -> RulesSeed:
    async with pg_factory() as s:
        cat = RuleCategory(code=f"{PREFIX}-FIRE", name="Пожары")
        other = RuleCategory(code=f"{PREFIX}-DTP", name="ДТП")
        itype = IncidentType(code=f"{PREFIX}-FIRE-BLD", name="Пожар в здании")
        s.add_all([cat, other, itype])
        await s.flush()
        result = RulesSeed(
            category_id=str(cat.id),
            other_category_id=str(other.id),
            incident_type_id=str(itype.id),
            prefix=PREFIX,
        )
        await s.commit()
        return result


@pytest_asyncio.fixture
async def api_client(
    pg_factory: async_sessionmaker, seed: RulesSeed
) -> AsyncGenerator[AsyncClient]:
    app = create_app()

    async def _override() -> AsyncGenerator:
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


def rule_payload(seed: RulesSeed, *, code: str, publish: bool = True) -> dict:
    """Build a valid ``RuleCreate`` body for the API."""
    return {
        "code": code,
        "name": "Пожар в здании — базовый выезд",
        "description": "Минимальный состав для пожара в здании",
        "category_id": seed.category_id,
        "is_enabled": True,
        "incident_type_ids": [seed.incident_type_id],
        "complexities": ["moderate"],
        "tags": ["fire", "building"],
        "publish": publish,
        "version": {
            "priority": "high",
            "notes": "v1",
            "conditions": [
                {
                    "condition_type": "incident_type",
                    "operator": "in",
                    "field": "incident_type_code",
                    "value": {"values": [f"{seed.prefix}-FIRE-BLD"]},
                }
            ],
            "actions": [
                {
                    "action_type": "require_resources",
                    "parameters": {},
                    "sort_order": 0,
                }
            ],
            "resource_requirements": [
                {
                    "resource_category": "vehicle",
                    "min_count": 2,
                    "recommended_count": 3,
                    "reserve_count": 1,
                    "priority": "high",
                }
            ],
            "capability_requirements": [
                {
                    "capability_code": "fire_suppression",
                    "min_quantity": 1,
                    "mandatory": True,
                }
            ],
        },
    }
