"""ORM models package.

Import every concrete model module here so that Alembic's autogenerate sees the
full metadata. Domain models will be added in later iterations — the base
primitives are ready and no architectural change is required to extend them.
"""

from app.models.base import IdentifiableBase

__all__ = ["IdentifiableBase"]
