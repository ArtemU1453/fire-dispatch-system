"""Fixtures for administration integration tests (skip if no PostgreSQL).

Seeds two permissions and a role (with both permissions) so RBAC, user and role
management can be exercised. Each run uses a unique prefix and cleans up its own
rows (including the audit entries it wrote, matched by actor name).
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
from app.models.security import Permission, Role, RolePermission

PREFIX = f"AD{uuid4().hex[:8]}"
ACTOR = f"{PREFIX}-admin"

# Catalog tables a directory test might add rows to (cleaned by code prefix).
_CATALOG_TABLES = (
    "incident_types", "resource_types", "vehicle_types", "personnel_roles",
    "equipment_types", "capabilities", "availability_statuses",
    "organizations", "account_statuses", "integration_providers",
)


@dataclass
class AdminSeed:
    prefix: str
    actor: str
    perm_read_id: str
    perm_write_id: str
    role_id: str


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
                "DELETE FROM audit_logs WHERE (changes->>'_actor_name') LIKE :p "
                "OR user_id IN (SELECT id FROM users WHERE username LIKE :p)"
            ),
            {"p": p},
        )
        await s.execute(
            text("DELETE FROM app_setting_history WHERE key LIKE :p"), {"p": p}
        )
        await s.execute(text("DELETE FROM app_settings WHERE key LIKE :p"), {"p": p})
        await s.execute(text("DELETE FROM integrations WHERE code LIKE :p"), {"p": p})
        for table in ("permission_groups", "roles", "permissions"):
            await s.execute(
                text(f"DELETE FROM {table} WHERE code LIKE :p"), {"p": p}
            )
        await s.execute(text("DELETE FROM users WHERE username LIKE :p"), {"p": p})
        for table in _CATALOG_TABLES:
            await s.execute(
                text(f"DELETE FROM {table} WHERE code LIKE :p"), {"p": p}
            )
        await s.commit()


@pytest_asyncio.fixture
async def seed(pg_factory: async_sessionmaker) -> AdminSeed:
    async with pg_factory() as s:
        read = Permission(code=f"{PREFIX}-users.read", name="Чтение пользователей")
        write = Permission(code=f"{PREFIX}-users.write", name="Изменение пользователей")
        role = Role(code=f"{PREFIX}-role", name="Администратор")
        s.add_all([read, write, role])
        await s.flush()
        s.add_all([
            RolePermission(role_id=role.id, permission_id=read.id),
            RolePermission(role_id=role.id, permission_id=write.id),
        ])
        result = AdminSeed(
            prefix=PREFIX, actor=ACTOR,
            perm_read_id=str(read.id), perm_write_id=str(write.id),
            role_id=str(role.id),
        )
        await s.commit()
        return result


@pytest_asyncio.fixture
async def api_client(
    pg_factory: async_sessionmaker, seed: AdminSeed
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
