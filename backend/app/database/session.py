"""Database engine and session management.

Provides a single async engine and a session factory. The
:func:`get_db_session` dependency yields a scoped ``AsyncSession`` and is the
only sanctioned way for the application layer to obtain a database connection
(Dependency Injection). Transaction lifecycle (commit / rollback / close) is
handled here so callers never have to.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

_settings = get_settings()

# The async engine is created once and reused for the whole application life.
engine: AsyncEngine = create_async_engine(
    _settings.SQLALCHEMY_DATABASE_URI,
    echo=_settings.DB_ECHO,
    pool_size=_settings.DB_POOL_SIZE,
    max_overflow=_settings.DB_MAX_OVERFLOW,
    pool_pre_ping=_settings.DB_POOL_PRE_PING,
    future=True,
)

# ``expire_on_commit=False`` keeps ORM objects usable after commit, which is the
# usual expectation in a request/response cycle.
SessionFactory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    """FastAPI dependency that yields a transactional ``AsyncSession``.

    The session is committed on success and rolled back on any exception, then
    always closed. This gives every request a clean unit-of-work boundary.
    """
    async with SessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
