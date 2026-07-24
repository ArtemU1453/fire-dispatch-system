"""Generic repository implementing the Repository Pattern.

The repository isolates persistence concerns from the service layer (Clean
Architecture / Dependency Inversion): services depend on the abstract
``AbstractRepository`` interface, not on SQLAlchemy. ``SqlAlchemyRepository``
provides a reusable, typed implementation of CRUD **plus filtering, sorting and
pagination** so concrete repositories need almost no code (DRY / KISS).

Soft-delete is first-class: reads exclude ``is_deleted`` rows by default and
``delete`` performs a logical delete when the model supports it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import Base, SoftDeleteMixin

ModelT = TypeVar("ModelT", bound=Base)


@dataclass(slots=True)
class Page(Generic[ModelT]):
    """A page of results plus the total count (for pagination metadata)."""

    items: Sequence[ModelT]
    total: int
    limit: int
    offset: int


@dataclass(slots=True)
class QuerySpec:
    """Declarative query options understood by :meth:`SqlAlchemyRepository.list`.

    Keeps the repository API small while supporting the required features:

    - ``filters``   — equality filters ``{column: value}`` (value may be a list
      for ``IN`` matching).
    - ``order_by``  — column names; prefix with ``-`` for descending.
    - ``limit`` / ``offset`` — pagination window.
    - ``include_deleted`` — bypass the default soft-delete exclusion.
    """

    filters: dict[str, Any] = field(default_factory=dict)
    order_by: Sequence[str] = field(default_factory=list)
    limit: int = 50
    offset: int = 0
    include_deleted: bool = False


class AbstractRepository(ABC, Generic[ModelT]):
    """Persistence-agnostic repository interface.

    Service-layer code type-hints against this interface so the concrete data
    store can be swapped (e.g. an in-memory fake in tests) without touching
    business logic.
    """

    @abstractmethod
    async def get(self, entity_id: Any) -> ModelT | None: ...

    @abstractmethod
    async def list(self, spec: QuerySpec | None = None) -> Sequence[ModelT]: ...

    @abstractmethod
    async def paginate(self, spec: QuerySpec | None = None) -> Page[ModelT]: ...

    @abstractmethod
    async def add(self, entity: ModelT) -> ModelT: ...

    @abstractmethod
    async def update(self, entity: ModelT, values: dict[str, Any]) -> ModelT: ...

    @abstractmethod
    async def delete(self, entity_id: Any, *, hard: bool = False) -> None: ...

    @abstractmethod
    async def count(self, spec: QuerySpec | None = None) -> int: ...


class SqlAlchemyRepository(AbstractRepository[ModelT], Generic[ModelT]):
    """Reusable async SQLAlchemy implementation of :class:`AbstractRepository`.

    Concrete repositories subclass this and set :attr:`model`. Flushing (not
    committing) keeps transaction control in the session dependency, honouring
    the unit-of-work boundary defined in :mod:`app.database.session`.
    """

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------ reads
    async def get(self, entity_id: Any) -> ModelT | None:
        entity = await self._session.get(self.model, entity_id)
        if entity is not None and self._is_soft_deleted(entity):
            return None
        return entity

    async def list(self, spec: QuerySpec | None = None) -> Sequence[ModelT]:
        spec = spec or QuerySpec()
        stmt = self._apply_pagination(self._build_query(spec), spec)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def paginate(self, spec: QuerySpec | None = None) -> Page[ModelT]:
        spec = spec or QuerySpec()
        items = await self.list(spec)
        total = await self.count(spec)
        return Page(items=items, total=total, limit=spec.limit, offset=spec.offset)

    async def count(self, spec: QuerySpec | None = None) -> int:
        spec = spec or QuerySpec()
        base = self._build_query(spec, for_count=True)
        result = await self._session.execute(
            select(func.count()).select_from(base.subquery())
        )
        return int(result.scalar_one())

    # ----------------------------------------------------------------- writes
    async def add(self, entity: ModelT) -> ModelT:
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def update(self, entity: ModelT, values: dict[str, Any]) -> ModelT:
        for key, value in values.items():
            setattr(entity, key, value)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def delete(self, entity_id: Any, *, hard: bool = False) -> None:
        """Soft-delete by default; ``hard=True`` removes the row physically."""
        if not hard and issubclass(self.model, SoftDeleteMixin):
            entity = await self._session.get(self.model, entity_id)
            if entity is not None:
                entity.is_deleted = True
                await self._session.flush()
            return
        await self._session.execute(
            delete(self.model).where(self.model.id == entity_id)  # type: ignore[attr-defined]
        )

    # ---------------------------------------------------------------- helpers
    def _build_query(
        self, spec: QuerySpec, *, for_count: bool = False
    ) -> Select[tuple[ModelT]]:
        stmt: Select[tuple[ModelT]] = select(self.model)
        stmt = self._apply_soft_delete(stmt, spec)
        stmt = self._apply_filters(stmt, spec)
        if not for_count:
            stmt = self._apply_ordering(stmt, spec)
        return stmt

    def _apply_soft_delete(
        self, stmt: Select[tuple[ModelT]], spec: QuerySpec
    ) -> Select[tuple[ModelT]]:
        if not spec.include_deleted and issubclass(self.model, SoftDeleteMixin):
            stmt = stmt.where(self.model.is_deleted.is_(False))  # type: ignore[attr-defined]
        return stmt

    def _apply_filters(
        self, stmt: Select[tuple[ModelT]], spec: QuerySpec
    ) -> Select[tuple[ModelT]]:
        for name, value in spec.filters.items():
            column = getattr(self.model, name, None)
            if column is None:
                raise ValueError(f"Unknown filter column: {name!r}")
            if isinstance(value, (list, tuple, set)):
                stmt = stmt.where(column.in_(value))
            else:
                stmt = stmt.where(column == value)
        return stmt

    def _apply_ordering(
        self, stmt: Select[tuple[ModelT]], spec: QuerySpec
    ) -> Select[tuple[ModelT]]:
        for token in spec.order_by:
            descending = token.startswith("-")
            name = token[1:] if descending else token
            column = getattr(self.model, name, None)
            if column is None:
                raise ValueError(f"Unknown order_by column: {name!r}")
            stmt = stmt.order_by(column.desc() if descending else column.asc())
        return stmt

    def _apply_pagination(
        self, stmt: Select[tuple[ModelT]], spec: QuerySpec
    ) -> Select[tuple[ModelT]]:
        return stmt.limit(spec.limit).offset(spec.offset)

    @staticmethod
    def _is_soft_deleted(entity: ModelT) -> bool:
        return bool(getattr(entity, "is_deleted", False))
