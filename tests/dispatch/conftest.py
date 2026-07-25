"""Fixtures for dispatch integration tests (skip if no PostgreSQL/PostGIS).

Seeds a self-contained scenario: an incident type, capabilities, availability
statuses, an organization, vehicles with capabilities near a reference point, and
a **published, active rule** (in the database Rule Engine) that requires the
``fire_suppression`` capability and a minimum vehicle composition. Each run uses a
unique code prefix and cleans up only its own rows.
"""

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
from app.gis.cache import InMemoryGeoCache
from app.gis.providers import FakeGeoProvider
from app.main import create_app
from app.models import (
    AvailabilityStatus,
    Capability,
    IncidentType,
    Organization,
    Resource,
    ResourceCapability,
    ResourceType,
)
from app.models.enums import ResourceCategory
from app.rules.models import RuleCategory
from app.rules.models.enums import ActionType, RulePriority
from app.rules.schemas.content import (
    ActionInput,
    CapabilityRequirementInput,
    ResourceRequirementInput,
    VersionContentInput,
)
from app.rules.schemas.rule import RuleCreate
from app.rules.services.versioning import RuleWriteService
from app.search.cache import create_search_cache

PREFIX = f"D{uuid4().hex[:8]}"
REF_LAT, REF_LON = 55.7539, 37.6208


@dataclass
class DispatchSeed:
    prefix: str
    incident_type_id: str
    organization_id: str
    near_id: str
    mid_id: str
    busy_id: str


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
                "DELETE FROM dispatch_recommendations WHERE incident_type_id IN "
                "(SELECT id FROM incident_types WHERE code LIKE :p)"
            ),
            {"p": p},
        )
        for table in (
            "rules",
            "rule_categories",
            "resources",
            "capabilities",
            "availability_statuses",
            "resource_types",
            "organizations",
            "incident_types",
        ):
            await s.execute(
                text(f"DELETE FROM {table} WHERE code LIKE :p"), {"p": p}
            )
        await s.commit()


@pytest_asyncio.fixture
async def seed(pg_factory: async_sessionmaker) -> DispatchSeed:
    async with pg_factory() as s:
        itype = IncidentType(code=f"{PREFIX}-FIRE", name="Пожар")
        vt = ResourceType(
            code=f"{PREFIX}-AC", name="АЦ", category=ResourceCategory.VEHICLE
        )
        org = Organization(code=f"{PREFIX}-PCH1", name="ПЧ-1")
        available = AvailabilityStatus(
            code=f"{PREFIX}-AV", name="Свободен",
            is_available_for_dispatch=True, is_operational=True, sort_order=1,
        )
        busy = AvailabilityStatus(
            code=f"{PREFIX}-BUSY", name="Занят",
            is_available_for_dispatch=False, is_operational=True, sort_order=5,
        )
        fs = Capability(code=f"{PREFIX}-fire_suppression", name="Пожаротушение")
        ws = Capability(code=f"{PREFIX}-water_supply", name="Водоснабжение")
        s.add_all([itype, vt, org, available, busy, fs, ws])
        await s.flush()

        ids: dict[str, str] = {}

        async def mk(code, lat, lon, status_id, caps):
            r = Resource(
                code=f"{PREFIX}-{code}", name=code,
                resource_type_id=vt.id, organization_id=org.id,
                availability_status_id=status_id, latitude=lat, longitude=lon,
                geom=WKTElement(f"POINT({lon} {lat})", srid=4326),
            )
            s.add(r)
            await s.flush()
            ids[code] = str(r.id)
            for cid, qty in caps:
                s.add(
                    ResourceCapability(
                        resource_id=r.id, capability_id=cid, quantity=qty
                    )
                )

        await mk("NEAR", 55.7520, 37.6175, available.id, [(fs.id, 1), (ws.id, 1)])
        await mk("MID", 55.7600, 37.6300, available.id, [(fs.id, 1)])
        await mk("BUSY", 55.7521, 37.6176, busy.id, [(fs.id, 1), (ws.id, 1)])
        await mk("FAR", 59.9343, 30.3351, available.id, [(fs.id, 2)])

        category = RuleCategory(code=f"{PREFIX}-CAT", name="Пожары")
        s.add(category)
        await s.flush()

        rule = RuleCreate(
            code=f"{PREFIX}-RULE",
            name="Пожар — базовый выезд",
            category_id=category.id,
            incident_type_ids=[itype.id],
            complexities=[],
            tags=["fire"],
            publish=True,
            version=VersionContentInput(
                priority=RulePriority.HIGH,
                actions=[ActionInput(action_type=ActionType.REQUIRE_RESOURCES)],
                resource_requirements=[
                    ResourceRequirementInput(
                        resource_category=ResourceCategory.VEHICLE,
                        min_count=1, recommended_count=2, reserve_count=1,
                        priority=RulePriority.HIGH,
                    )
                ],
                capability_requirements=[
                    CapabilityRequirementInput(
                        capability_code=f"{PREFIX}-fire_suppression",
                        min_quantity=1, mandatory=True,
                    )
                ],
            ),
        )
        await RuleWriteService(s).create_rule(rule)
        await s.commit()

        return DispatchSeed(
            prefix=PREFIX,
            incident_type_id=str(itype.id),
            organization_id=str(org.id),
            near_id=ids["NEAR"],
            mid_id=ids["MID"],
            busy_id=ids["BUSY"],
        )


@pytest_asyncio.fixture
async def api_client(
    pg_factory: async_sessionmaker, seed: DispatchSeed
) -> AsyncGenerator[AsyncClient]:
    app = create_app()
    app.state.geo_provider = FakeGeoProvider()
    app.state.geo_cache = InMemoryGeoCache()
    app.state.search_cache = create_search_cache()

    async def _override():
        async with pg_factory() as s:
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise

    app.dependency_overrides[get_db_session] = _override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        yield c
    app.dependency_overrides.clear()
