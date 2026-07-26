"""Fixtures for analytics tests (skip if no PostgreSQL).

Seeds a small, deterministic dataset (3 calls, 3 incidents, 1 dispatch, 2 unit
assignments, 1 dispatcher) so KPIs and statistics have known values, then cleans
up its own rows by prefix.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.calls.models.entities import Call
from app.config import get_settings
from app.database import get_db_session
from app.incidents.models.entities import Incident, IncidentDispatch
from app.incidents.models.enums import (
    IncidentCategory,
    IncidentPriority,
    IncidentSource,
    IncidentStatus,
)
from app.main import create_app
from app.models import AdministrativeArea, IncidentType, Organization, ResourceType
from app.models.enums import ResourceCategory
from app.models.resource import Resource
from app.resources.models.entities import ResourceAssignment, Unit

PREFIX = f"AN{uuid4().hex[:8]}"
BASE = datetime.now(tz=UTC) - timedelta(hours=1)


@dataclass
class AnalyticsSeed:
    prefix: str
    incident_type_name: str
    area_name: str
    unit_id: str
    user_id: str


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
        await s.execute(
            text(
                "DELETE FROM audit_logs WHERE entity_type = 'analytics_export' "
                "AND (changes->>'_actor_name') LIKE :p"
            ),
            {"p": p},
        )
        await s.execute(
            text(
                "DELETE FROM resource_assignments WHERE unit_id IN "
                "(SELECT id FROM units WHERE code LIKE :p)"
            ),
            {"p": p},
        )
        await s.execute(text("DELETE FROM calls WHERE number LIKE :p"), {"p": p})
        await s.execute(text("DELETE FROM incidents WHERE number LIKE :p"), {"p": p})
        await s.execute(text("DELETE FROM units WHERE code LIKE :p"), {"p": p})
        await s.execute(text("DELETE FROM resources WHERE code LIKE :p"), {"p": p})
        await s.execute(text("DELETE FROM users WHERE username LIKE :p"), {"p": p})
        for table in (
            "incident_types", "administrative_areas", "organizations",
            "resource_types",
        ):
            await s.execute(
                text(f"DELETE FROM {table} WHERE code LIKE :p"), {"p": p}
            )
        await s.commit()


@pytest_asyncio.fixture
async def seed(pg_factory: async_sessionmaker) -> AnalyticsSeed:
    async with pg_factory() as s:
        org = Organization(code=f"{PREFIX}-ORG", name="ПЧ-1")
        itype = IncidentType(code=f"{PREFIX}-FIRE", name="Пожар")
        area = AdministrativeArea(code=f"{PREFIX}-AREA", name="Центральный район")
        vt = ResourceType(
            code=f"{PREFIX}-VT", name="АЦ", category=ResourceCategory.VEHICLE
        )
        s.add_all([org, itype, area, vt])
        await s.flush()

        resource = Resource(
            code=f"{PREFIX}-VEH", name="Автоцистерна",
            resource_type_id=vt.id, organization_id=org.id,
        )
        unit = Unit(code=f"{PREFIX}-U1", name="Отделение 1", organization_id=org.id)
        from app.admin.utils.passwords import hash_password
        from app.models.security import User

        user = User(
            username=f"{PREFIX}-disp", email=f"{PREFIX}@x.io",
            hashed_password=hash_password("Str0ngPass1"),
        )
        s.add_all([resource, unit, user])
        await s.flush()

        # 3 incidents (2 confirmed), all in the same type + district.
        incidents = []
        for i in range(3):
            inc = Incident(
                number=f"{PREFIX}-INC{i}",
                incident_type_id=itype.id,
                administrative_area_id=area.id,
                category=IncidentCategory.FIRE,
                source=IncidentSource.PHONE,
                status=IncidentStatus.CREATED,
                priority=IncidentPriority.NORMAL,
                reported_at=BASE,
                confirmed_at=BASE + timedelta(seconds=60) if i < 2 else None,
            )
            incidents.append(inc)
        s.add_all(incidents)
        await s.flush()

        # 3 calls with known wait times (avg = 20s), all one dispatcher.
        for i, wait in enumerate((10, 20, 30)):
            s.add(Call(
                number=f"{PREFIX}-CALL{i}",
                received_at=BASE,
                answered_at=BASE + timedelta(seconds=wait),
                wait_seconds=wait,
                dispatcher_user_id=user.id,
            ))

        # 1 dispatch (assignment time 120s) + 2 unit assignments.
        s.add(IncidentDispatch(
            incident_id=incidents[0].id, resource_id=resource.id,
            assigned_at=BASE + timedelta(seconds=120),
        ))
        s.add_all([
            ResourceAssignment(unit_id=unit.id, incident_id=incidents[0].id,
                               assigned_at=BASE),
            ResourceAssignment(unit_id=unit.id, incident_id=incidents[1].id,
                               assigned_at=BASE),
        ])

        result = AnalyticsSeed(
            prefix=PREFIX, incident_type_name="Пожар",
            area_name="Центральный район",
            unit_id=str(unit.id), user_id=str(user.id),
        )
        await s.commit()
        return result


@pytest_asyncio.fixture
async def api_client(
    pg_factory: async_sessionmaker, seed: AnalyticsSeed
) -> AsyncGenerator[AsyncClient]:
    from app.analytics.utils.cache import analytics_cache

    analytics_cache.clear()
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
    analytics_cache.clear()
