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
