"""Generic repository implementing the Repository Pattern.

The repository isolates persistence concerns from the service layer (Clean
Architecture / Dependency Inversion): services depend on the abstract
``AbstractRepository`` interface, not on SQLAlchemy. ``SqlAlchemyRepository``
provides a reusable, typed CRUD implementation so concrete repositories need
almost no code (DRY / KISS).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class AbstractRepository(ABC, Generic[ModelT]):
    """Persistence-agnostic repository interface.

    Service-layer code should type-hint against this interface so the concrete
    data store can be swapped (e.g. for an in-memory fake in tests) without
    touching business logic.
    """

    @abstractmethod
    async def get(self, entity_id: Any) -> ModelT | None: ...

    @abstractmethod
    async def list(self, *, limit: int = 100, offset: int = 0) -> Sequence[ModelT]: ...

    @abstractmethod
    async def add(self, entity: ModelT) -> ModelT: ...

    @abstractmethod
    async def delete(self, entity_id: Any) -> None: ...

    @abstractmethod
    async def count(self) -> int: ...


class SqlAlchemyRepository(AbstractRepository[ModelT], Generic[ModelT]):
    """Reusable async SQLAlchemy implementation of :class:`AbstractRepository`.

    Concrete repositories subclass this and set :attr:`model`. Flushing (not
    committing) keeps transaction control in the session dependency, honouring
    the unit-of-work boundary defined in :mod:`app.database.session`.
    """

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, entity_id: Any) -> ModelT | None:
        return await self._session.get(self.model, entity_id)

    async def list(
        self, *, limit: int = 100, offset: int = 0
    ) -> Sequence[ModelT]:
        result = await self._session.execute(
            select(self.model).limit(limit).offset(offset)
        )
        return result.scalars().all()

    async def add(self, entity: ModelT) -> ModelT:
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def delete(self, entity_id: Any) -> None:
        await self._session.execute(
            delete(self.model).where(self.model.id == entity_id)  # type: ignore[attr-defined]
        )

    async def count(self) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(self.model)
        )
        return int(result.scalar_one())
