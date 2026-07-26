#!/usr/bin/env bash
# =========================================================================
# Enforce the backup retention policy (Stage 16 §3).
# Deletes backup artefacts older than BACKUP_RETENTION_DAYS. Run from cron
# after backup_all.sh. Retention is configurable per environment.
#
# Usage: BACKUP_RETENTION_DAYS=30 scripts/backup/prune_backups.sh
# =========================================================================
. "$(cd "$(dirname "$0")/.." && pwd)/lib/common.sh"

[ -d "$BACKUP_DIR" ] || { log "no backup dir '$BACKUP_DIR'; nothing to prune"; exit 0; }

log "Pruning backups older than ${BACKUP_RETENTION_DAYS} days under $BACKUP_DIR"
before=$(find "$BACKUP_DIR" -type f \( -name '*.dump' -o -name '*.tar.gz' -o -name '*.revision' \) | wc -l)
find "$BACKUP_DIR" -type f \
  \( -name '*.dump' -o -name '*.tar.gz' -o -name '*.revision' \) \
  -mtime +"$BACKUP_RETENTION_DAYS" -print -delete
after=$(find "$BACKUP_DIR" -type f \( -name '*.dump' -o -name '*.tar.gz' -o -name '*.revision' \) | wc -l)
log "Prune complete: $((before - after)) file(s) removed, $after retained"
