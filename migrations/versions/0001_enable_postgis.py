"""enable postgis extension

Revision ID: 0001_enable_postgis
Revises:
Create Date: 2026-07-24

The very first migration provisions the PostGIS extension so a fresh database
gains spatial types before any table that uses them is created. Kept separate
from the schema migration so the extension concern is explicit and reusable.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_enable_postgis"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")


def downgrade() -> None:
    # Intentionally a no-op: PostGIS is a cluster/database-wide extension that
    # may be shared by other schemas and is often owned by a superuser. Dropping
    # it on downgrade is unsafe and privilege-sensitive, so we leave it in place.
    pass
