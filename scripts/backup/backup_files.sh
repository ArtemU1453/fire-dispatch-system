#!/usr/bin/env bash
# =========================================================================
# Back up configuration, logs and uploaded files (Stage 16 §3).
# Each category is a separate compressed tarball so it can be restored
# independently. Secrets are explicitly excluded — they live in the secrets
# manager, not in backups.
#
# Usage: scripts/backup/backup_files.sh [output_dir]
# =========================================================================
. "$(cd "$(dirname "$0")/.." && pwd)/lib/common.sh"

require_cmd tar

OUT_DIR="${1:-$BACKUP_DIR/files}"
mkdir -p "$OUT_DIR"
TS="$(timestamp)"

archive() {
  local name="$1" src="$2"
  if [ ! -d "$src" ]; then
    log "skip $name: '$src' does not exist"
    return 0
  fi
  local out="$OUT_DIR/${name}_${TS}.tar.gz"
  log "Archiving $name from $src -> $out"
  # Exclude any accidental secret material and Python caches.
  tar --exclude='*.pem' --exclude='*.key' --exclude='.env' \
      --exclude='__pycache__' -czf "$out" -C "$(dirname "$src")" "$(basename "$src")"
  log "  $name backup: $out ($(du -h "$out" | cut -f1))"
}

archive config  "$BACKUP_CONFIG_DIR"
archive logs    "$BACKUP_LOG_DIR"
archive uploads "$BACKUP_UPLOADS_DIR"

log "File backups complete under $OUT_DIR"
