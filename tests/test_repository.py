"""Behavioural tests for the generic repository.

Exercised against in-memory SQLite using a non-spatial model (``Organization``)
so the suite stays hermetic while still covering CRUD, filtering, sorting,
pagination and soft-delete on the real :class:`SqlAlchemyRepository`.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.models import Organization
from app.repositories import OrganizationRepository, QuerySpec


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Organization.__table__.create)
    async with async_sessionmaker(engine, expire_on_commit=False)() as s:
        yield s
    await engine.dispose()


@pytest_asyncio.fixture
async def repo(session: AsyncSession) -> OrganizationRepository:
    r = OrganizationRepository(session)
    for i in range(5):
        await r.add(Organization(code=f"ORG-{i}", name=f"Org {i}"))
    await session.flush()
    return r


@pytest.mark.asyncio
async def test_add_sets_audit_fields(repo: OrganizationRepository) -> None:
    org = await repo.add(Organization(code="NEW", name="New Org"))
    assert org.id is not None
    assert org.created_at is not None
    assert org.is_deleted is False


@pytest.mark.asyncio
async def test_filter_equality(repo: OrganizationRepository) -> None:
    items = await repo.list(QuerySpec(filters={"code": "ORG-2"}))
    assert [o.code for o in items] == ["ORG-2"]


@pytest.mark.asyncio
async def test_filter_in_list(repo: OrganizationRepository) -> None:
    items = await repo.list(QuerySpec(filters={"code": ["ORG-1", "ORG-3"]}))
    assert {o.code for o in items} == {"ORG-1", "ORG-3"}


@pytest.mark.asyncio
async def test_sorting_descending(repo: OrganizationRepository) -> None:
    items = await repo.list(QuerySpec(order_by=["-code"]))
    assert [o.code for o in items] == ["ORG-4", "ORG-3", "ORG-2", "ORG-1", "ORG-0"]


@pytest.mark.asyncio
async def test_pagination(repo: OrganizationRepository) -> None:
    page = await repo.paginate(QuerySpec(order_by=["code"], limit=2, offset=2))
    assert page.total == 5
    assert page.limit == 2 and page.offset == 2
    assert [o.code for o in page.items] == ["ORG-2", "ORG-3"]


@pytest.mark.asyncio
async def test_update(repo: OrganizationRepository) -> None:
    org = (await repo.list(QuerySpec(filters={"code": "ORG-0"})))[0]
    await repo.update(org, {"name": "Renamed"})
    assert (await repo.get(org.id)).name == "Renamed"


@pytest.mark.asyncio
async def test_soft_delete_hides_row(repo: OrganizationRepository) -> None:
    org = (await repo.list(QuerySpec(filters={"code": "ORG-0"})))[0]
    await repo.delete(org.id)
    assert await repo.get(org.id) is None
    assert await repo.count() == 4
    # still present when explicitly including deleted
    including = await repo.list(QuerySpec(include_deleted=True))
    assert any(o.id == org.id for o in including)


@pytest.mark.asyncio
async def test_unknown_filter_column_raises(repo: OrganizationRepository) -> None:
    with pytest.raises(ValueError):
        await repo.list(QuerySpec(filters={"nope": 1}))
