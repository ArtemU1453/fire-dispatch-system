"""Fixtures for resource-management integration tests (skip if no PostgreSQL).

The 9 standard statuses are seeded by the migration, so tests reference them by
code (``free``, ``on_scene``, …). Each run seeds an organization, a vehicle and a
personnel resource, a unit (bound to the vehicle), a crew and an incident, then
cleans up only its own rows.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import dataclass
from uuid import uuid4

import pytest
import pytest_asyncio
from geoalchemy2 import WKTElement
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import get_settings
from app.database import get_db_session
from app.incidents.models import Incident
from app.main import create_app
from app.models import (
    AvailabilityStatus,
    Organization,
    Personnel,
    PersonnelRole,
    Resource,
    ResourceType,
    Vehicle,
    VehicleType,
)
from app.models.enums import ResourceCategory
from app.resources.models import Crew, CrewMember, Unit

PREFIX = f"R{uuid4().hex[:8]}"

# The 9 standard statuses the migration seeds (code, name, operational,
# dispatchable, sort_order). Re-ensured here so these tests stay green even when
# another suite's fixtures wipe the shared ``availability_statuses`` table.
_STATUSES = [
    ("on_duty", "В боевом расчёте", True, True, 10),
    ("free", "Свободно", True, True, 20),
    ("enroute", "Следует к месту вызова", True, False, 30),
    ("on_scene", "Работает на месте", True, False, 40),
    ("returning", "Возвращается", True, False, 50),
    ("maintenance", "На обслуживании", False, False, 60),
    ("repair", "На ремонте", False, False, 70),
    ("unavailable", "Недоступно", False, False, 80),
    ("reserve", "Резерв", True, False, 90),
]


async def _ensure_statuses(s) -> None:
    """Idempotently (re)seed the 9 standard availability statuses."""
    for code, name, operational, dispatchable, order in _STATUSES:
        await s.execute(
            text(
                "INSERT INTO availability_statuses "
                "(id, code, name, is_operational, is_available_for_dispatch, "
                " sort_order, is_deleted, created_at, updated_at) "
                "VALUES (gen_random_uuid(), :code, :name, :op, :disp, :ord, "
                " false, now(), now()) "
                "ON CONFLICT (code) DO NOTHING"
            ),
            {
                "code": code, "name": name, "op": operational,
                "disp": dispatchable, "ord": order,
            },
        )


@dataclass
class ResourceSeed:
    prefix: str
    unit_id: str
    vehicle_resource_id: str
    personnel_resource_id: str
    crew_id: str
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
        await s.execute(
            text(
                "DELETE FROM resource_management_history WHERE resource_id IN "
                "(SELECT id FROM resources WHERE code LIKE :p) "
                "OR unit_id IN (SELECT id FROM units WHERE code LIKE :p)"
            ),
            {"p": p},
        )
        await s.execute(
            text(
                "DELETE FROM status_history WHERE resource_id IN "
                "(SELECT id FROM resources WHERE code LIKE :p)"
            ),
            {"p": p},
        )
        for table in ("units", "crews", "shifts"):
            await s.execute(
                text(f"DELETE FROM {table} WHERE code LIKE :p"), {"p": p}
            )
        await s.execute(text("DELETE FROM incidents WHERE number LIKE :p"), {"p": p})
        # resources first (CASCADEs to vehicles/personnel); the RESTRICT-ed
        # catalog rows they referenced can only go afterwards.
        for table in (
            "resources", "resource_types", "vehicle_types",
            "personnel_roles", "organizations",
        ):
            await s.execute(
                text(f"DELETE FROM {table} WHERE code LIKE :p"), {"p": p}
            )
        await s.commit()


@pytest_asyncio.fixture
async def seed(pg_factory: async_sessionmaker) -> ResourceSeed:
    async with pg_factory() as s:
        await _ensure_statuses(s)
        free = (
            await s.execute(
                select(AvailabilityStatus).where(AvailabilityStatus.code == "free")
            )
        ).scalars().first()
        org = Organization(code=f"{PREFIX}-ORG", name="ПЧ-1")
        vt = ResourceType(
            code=f"{PREFIX}-VT", name="АЦ", category=ResourceCategory.VEHICLE
        )
        pt = ResourceType(
            code=f"{PREFIX}-PT", name="Боец", category=ResourceCategory.PERSONNEL
        )
        role = PersonnelRole(code=f"{PREFIX}-ROLE", name="Пожарный")
        veh_type = VehicleType(code=f"{PREFIX}-VTYPE", name="Автоцистерна")
        s.add_all([org, vt, pt, role, veh_type])
        await s.flush()

        vehicle_res = Resource(
            code=f"{PREFIX}-VEH", name="Автоцистерна 1",
            resource_type_id=vt.id, organization_id=org.id,
            availability_status_id=free.id if free else None,
            latitude=55.75, longitude=37.62,
            geom=WKTElement("POINT(37.62 55.75)", srid=4326),
        )
        person_res = Resource(
            code=f"{PREFIX}-PER", name="Иванов",
            resource_type_id=pt.id, organization_id=org.id,
            availability_status_id=free.id if free else None,
        )
        s.add_all([vehicle_res, person_res])
        await s.flush()
        s.add(
            Vehicle(
                resource_id=vehicle_res.id, vehicle_type_id=veh_type.id,
                plate_number="А001АА",
            )
        )
        s.add(
            Personnel(
                resource_id=person_res.id, personnel_role_id=role.id,
                first_name="Иван", last_name="Иванов", rank="сержант",
            )
        )

        unit = Unit(
            code=f"{PREFIX}-U1", name="Отделение 1",
            organization_id=org.id, vehicle_resource_id=vehicle_res.id,
            availability_status_id=free.id if free else None,
        )
        crew = Crew(code=f"{PREFIX}-C1", name="Караул 1", is_on_duty=True)
        s.add_all([unit, crew])
        await s.flush()
        s.add(
            CrewMember(
                crew_id=crew.id, personnel_resource_id=person_res.id,
                position="командир", is_commander=True,
            )
        )

        incident = Incident(number=f"{PREFIX}-INC", title="Пожар")
        s.add(incident)
        await s.flush()

        result = ResourceSeed(
            prefix=PREFIX,
            unit_id=str(unit.id),
            vehicle_resource_id=str(vehicle_res.id),
            personnel_resource_id=str(person_res.id),
            crew_id=str(crew.id),
            incident_id=str(incident.id),
        )
        await s.commit()
        return result


@pytest_asyncio.fixture
async def api_client(
    pg_factory: async_sessionmaker, seed: ResourceSeed
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
