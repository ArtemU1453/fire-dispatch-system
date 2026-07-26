#!/usr/bin/env bash
# =========================================================================
# Restore the PostgreSQL/PostGIS database from a custom-format dump (§4).
# Intended for disaster recovery. By default it restores into the configured
# target database; pass --create to (re)create a fresh database first.
#
# Usage: PGPASSWORD=... scripts/backup/restore_database.sh <dump_file> [--create]
#
# SAFETY: restoring overwrites data. The script requires CONFIRM=yes to run
# against a non-empty target unless --create is given.
# =========================================================================
. "$(cd "$(dirname "$0")/.." && pwd)/lib/common.sh"

require_cmd pg_restore
require_cmd psql

DUMP="${1:-}"
[ -n "$DUMP" ] || die "usage: restore_database.sh <dump_file> [--create]"
[ -f "$DUMP" ] || die "dump file not found: $DUMP"
CREATE="${2:-}"

PSQL=(psql --host="$POSTGRES_HOST" --port="$POSTGRES_PORT" --username="$POSTGRES_USER")

if [ "$CREATE" = "--create" ]; then
  log "Recreating database '$POSTGRES_DB'"
  "${PSQL[@]}" --dbname=postgres -v ON_ERROR_STOP=1 \
    -c "DROP DATABASE IF EXISTS \"$POSTGRES_DB\";" \
    -c "CREATE DATABASE \"$POSTGRES_DB\";"
  # PostGIS lives in its own extension; the dump recreates spatial objects but
  # the extension itself must exist first on a brand-new database.
  "${PSQL[@]}" --dbname="$POSTGRES_DB" -v ON_ERROR_STOP=1 \
    -c "CREATE EXTENSION IF NOT EXISTS postgis;"
else
  if [ "${CONFIRM:-no}" != "yes" ]; then
    die "target '$POSTGRES_DB' will be overwritten. Re-run with CONFIRM=yes or --create."
  fi
fi

log "Restoring $DUMP into '$POSTGRES_DB'"
# --clean --if-exists: drop objects before recreating so a partial DB is healed.
pg_restore \
  --host="$POSTGRES_HOST" --port="$POSTGRES_PORT" \
  --username="$POSTGRES_USER" --dbname="$POSTGRES_DB" \
  --clean --if-exists --no-owner --no-privileges \
  "$DUMP"

log "Restore complete. Verify schema with: alembic current"
