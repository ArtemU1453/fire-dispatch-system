#!/usr/bin/env bash
# =========================================================================
# Back up the PostgreSQL/PostGIS database (Stage 16 §3).
# Produces a compressed custom-format dump (pg_restore-ready) so single tables
# can be restored selectively during disaster recovery.
#
# Usage:   PGPASSWORD=... scripts/backup/backup_database.sh [output_dir]
# Restore: scripts/backup/restore_database.sh <dump_file>
# =========================================================================
. "$(cd "$(dirname "$0")/.." && pwd)/lib/common.sh"

require_cmd pg_dump

OUT_DIR="${1:-$BACKUP_DIR/database}"
mkdir -p "$OUT_DIR"
DUMP="$OUT_DIR/dispatcher_${POSTGRES_DB}_$(timestamp).dump"

log "Dumping database '$POSTGRES_DB' from $POSTGRES_HOST:$POSTGRES_PORT -> $DUMP"
# --format=custom: compressed, selective-restore capable.
# --no-owner/--no-privileges: portable across environments (roles differ).
pg_dump \
  --host="$POSTGRES_HOST" --port="$POSTGRES_PORT" \
  --username="$POSTGRES_USER" --dbname="$POSTGRES_DB" \
  --format=custom --compress=9 --no-owner --no-privileges \
  --file="$DUMP"

# Record the migration revision the dump was taken at, for restore validation.
if command -v alembic >/dev/null 2>&1; then
  alembic current 2>/dev/null | head -1 > "$DUMP.revision" || true
fi

log "Database backup complete: $DUMP ($(du -h "$DUMP" | cut -f1))"
echo "$DUMP"
