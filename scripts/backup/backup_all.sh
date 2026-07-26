#!/usr/bin/env bash
# =========================================================================
# Full backup orchestrator (Stage 16 §3): database + config + logs + uploads,
# followed by retention pruning. Suitable for a nightly cron / scheduled job.
#
# Usage: PGPASSWORD=... scripts/backup/backup_all.sh
# =========================================================================
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/../lib/common.sh"

log "=== Full backup starting (env=${APP_ENV:-unknown}) ==="
"$HERE/backup_database.sh"
"$HERE/backup_files.sh"
"$HERE/prune_backups.sh"
log "=== Full backup complete ==="
