"""Service-layer base class.

Services hold application/business logic and orchestrate repositories. They
receive their collaborators via the constructor (Dependency Injection) and never
construct sessions or engines themselves — keeping them pure and testable.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


class BaseService:
    """Common base for services that need a database session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
