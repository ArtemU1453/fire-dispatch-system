#!/usr/bin/env bash
# =========================================================================
# Migration verification (Stage 16 §8).
# Proves that the Alembic migration chain:
#   1. applies cleanly to head,
#   2. matches the SQLAlchemy models (no autogenerate drift),
#   3. downgrades all the way to base (rollback works), and
#   4. re-applies to head (round-trip is idempotent).
#
# Requires a reachable PostgreSQL/PostGIS database (env: POSTGRES_*). Used by
# `make migrate-check` and the CI pipeline.
# =========================================================================
set -euo pipefail

log() { printf '[migrations] %s\n' "$*" >&2; }

# Some PostGIS images (e.g. postgis/postgis) auto-install the Tiger geocoder and
# topology extensions, which create dozens of tables in the `tiger`/`topology`
# schemas. This application uses PostGIS geometry but NOT those extensions, so
# `alembic check` would otherwise report them as spurious drift. Drop them
# (best-effort) before the drift check so it compares only application-managed
# objects. `postgis` itself is kept. No-op if psql is unavailable or they are
# already absent.
if command -v psql >/dev/null 2>&1; then
  log "0/4 drop non-application PostGIS extensions (tiger geocoder, topology)"
  PGHOST="${POSTGRES_HOST:-localhost}" PGPORT="${POSTGRES_PORT:-5432}" \
  PGUSER="${POSTGRES_USER:-dispatcher}" PGDATABASE="${POSTGRES_DB:-dispatcher}" \
  PGPASSWORD="${PGPASSWORD:-${POSTGRES_PASSWORD:-}}" \
  psql -v ON_ERROR_STOP=0 -q \
    -c "DROP EXTENSION IF EXISTS postgis_tiger_geocoder CASCADE;" \
    -c "DROP EXTENSION IF EXISTS postgis_topology CASCADE;" \
    -c "DROP SCHEMA IF EXISTS tiger CASCADE;" \
    -c "DROP SCHEMA IF EXISTS tiger_data CASCADE;" \
    -c "DROP SCHEMA IF EXISTS topology CASCADE;" >/dev/null 2>&1 || \
    log "  (skipped: could not connect or nothing to drop)"
fi

log "1/4 upgrade -> head"
alembic upgrade head

log "2/4 check for model/migration drift"
# `alembic check` exits non-zero if autogenerate would produce operations,
# i.e. the models and the migration history have diverged.
alembic check

log "3/4 downgrade -> base (rollback)"
alembic downgrade base

log "4/4 re-upgrade -> head (round-trip)"
alembic upgrade head

log "OK: migrations apply, match models, roll back and round-trip cleanly."
