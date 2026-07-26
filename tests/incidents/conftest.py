"""Fixtures for incident-management integration tests (skip if no PostgreSQL).

Seeds an incident type, a deployable resource with a capability and a published
dispatch rule, so both the incident lifecycle and the Dispatch-Engine
integration (request_recommendation) can be exercised. Each run uses a unique
code prefix and cleans up only its own rows.
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

PREFIX = f"I{uuid4().hex[:8]}"
REF_LAT, REF_LON = 55.7539, 37.6208


@dataclass
class IncidentSeed:
    prefix: str
    incident_type_id: str
    resource_id: str


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
                "DELETE FROM incidents WHERE incident_type_id IN "
                "(SELECT id FROM incident_types WHERE code LIKE :p)"
            ),
            {"p": p},
        )
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
async def seed(pg_factory: async_sessionmaker) -> IncidentSeed:
    async with pg_factory() as s:
        itype = IncidentType(code=f"{PREFIX}-FIRE", name="Пожар")
        vt = ResourceType(
            code=f"{PREFIX}-AC", name="АЦ", category=ResourceCategory.VEHICLE
        )
        org = Organization(code=f"{PREFIX}-PCH", name="ПЧ-1")
        available = AvailabilityStatus(
            code=f"{PREFIX}-AV", name="Свободен",
            is_available_for_dispatch=True, is_operational=True, sort_order=1,
        )
        fs = Capability(code=f"{PREFIX}-fire_suppression", name="Пожаротушение")
        s.add_all([itype, vt, org, available, fs])
        await s.flush()

        resource = Resource(
            code=f"{PREFIX}-NEAR", name="Автоцистерна",
            resource_type_id=vt.id, organization_id=org.id,
            availability_status_id=available.id,
            latitude=55.7520, longitude=37.6175,
            geom=WKTElement("POINT(37.6175 55.7520)", srid=4326),
        )
        s.add(resource)
        await s.flush()
        s.add(
            ResourceCapability(
                resource_id=resource.id, capability_id=fs.id, quantity=1
            )
        )

        category = RuleCategory(code=f"{PREFIX}-CAT", name="Пожары")
        s.add(category)
        await s.flush()
        rule = RuleCreate(
            code=f"{PREFIX}-RULE",
            name="Пожар — базовый выезд",
            category_id=category.id,
            incident_type_ids=[itype.id],
            complexities=[],
            tags=[],
            publish=True,
            version=VersionContentInput(
                priority=RulePriority.HIGH,
                actions=[ActionInput(action_type=ActionType.REQUIRE_RESOURCES)],
                resource_requirements=[
                    ResourceRequirementInput(
                        resource_category=ResourceCategory.VEHICLE,
                        min_count=1, recommended_count=1,
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
        return IncidentSeed(
            prefix=PREFIX,
            incident_type_id=str(itype.id),
            resource_id=str(resource.id),
        )


@pytest_asyncio.fixture
async def api_client(
    pg_factory: async_sessionmaker, seed: IncidentSeed
) -> AsyncGenerator[AsyncClient]:
    from app.gis.cache import InMemoryGeoCache
    from app.gis.providers import FakeGeoProvider
    from app.routing.providers import HaversineRoutingProvider
    from app.routing.repositories import InMemoryRouteCache
    from app.search.cache import create_search_cache

    app = create_app()
    app.state.geo_provider = FakeGeoProvider()
    app.state.geo_cache = InMemoryGeoCache()
    app.state.search_cache = create_search_cache()
    app.state.route_provider = HaversineRoutingProvider()
    app.state.route_cache = InMemoryRouteCache()

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
