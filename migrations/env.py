"""Alembic migration environment.

Bridges Alembic with the application: it pulls the database URL and the ORM
metadata from the app itself, so migrations always match the code (single source
of truth). Uses the synchronous psycopg driver, which is the simplest and most
robust choice for the migration process.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from geoalchemy2 import alembic_helpers
from sqlalchemy import engine_from_config, pool

import app.calls.models  # noqa: F401  (side-effect: registers call models)
import app.dispatch.models  # noqa: F401  (side-effect: registers dispatch models)
import app.gis.models  # noqa: F401  (side-effect: registers GIS models)
import app.incidents.models  # noqa: F401  (side-effect: registers incident models)
import app.resources.models  # noqa: F401  (side-effect: registers resource-mgmt models)
import app.models  # noqa: F401  (side-effect: registers models)
import app.rules.models  # noqa: F401  (side-effect: registers rules models)
from app.config import get_settings

# Import Base and ensure all models are registered on its metadata.
from app.database.base import Base

# Alembic Config object providing access to values in alembic.ini.
config = context.config

# Inject the database URL from application settings (sync driver).
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.SQLALCHEMY_DATABASE_URI_SYNC)

# Configure Python logging from the ini file, if present.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata used for 'autogenerate' support.
target_metadata = Base.metadata


# Shared configuration for both modes. GeoAlchemy2's Alembic helpers make
# autogenerate PostGIS-aware: they render ``Geometry`` types, manage spatial
# (GiST) indexes, and exclude PostGIS-managed objects such as ``spatial_ref_sys``.
_COMMON_OPTS = dict(
    target_metadata=target_metadata,
    compare_type=True,
    include_object=alembic_helpers.include_object,
    render_item=alembic_helpers.render_item,
    process_revision_directives=alembic_helpers.writer,
)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL without a DB connection)."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **_COMMON_OPTS,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode against a live database connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, **_COMMON_OPTS)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
