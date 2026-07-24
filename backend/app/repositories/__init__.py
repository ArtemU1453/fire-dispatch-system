"""Repositories package (Repository Pattern).

Exposes the generic base classes. Concrete repositories for domain models are
added here later without altering the interface the service layer depends on.
"""

from app.repositories.base import AbstractRepository, SqlAlchemyRepository

__all__ = ["AbstractRepository", "SqlAlchemyRepository"]
