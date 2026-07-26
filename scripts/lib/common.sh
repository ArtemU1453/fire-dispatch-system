#!/usr/bin/env bash
# =========================================================================
# Shared helpers for the AI Dispatcher МЧС operational scripts.
# Source this file: `. "$(dirname "$0")/lib/common.sh"`
# It is platform-agnostic (no CI/CD or cloud vendor assumptions) and reads
# all connection parameters from the environment — never from the repo.
# =========================================================================
set -euo pipefail

log()  { printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >&2; }
die()  { log "ERROR: $*"; exit 1; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

# Database connection is assembled from the same variables the app uses, so
# there is a single source of truth. Passwords come from PGPASSWORD (which an
# operator populates from the secrets manager), never from a committed file.
: "${POSTGRES_HOST:=localhost}"
: "${POSTGRES_PORT:=5432}"
: "${POSTGRES_USER:=dispatcher}"
: "${POSTGRES_DB:=dispatcher}"

# Where backups live and how long they are kept (retention policy, §3).
: "${BACKUP_DIR:=/var/backups/dispatcher}"
: "${BACKUP_RETENTION_DAYS:=30}"        # daily backups pruned after N days
: "${BACKUP_UPLOADS_DIR:=/var/lib/dispatcher/uploads}"
: "${BACKUP_CONFIG_DIR:=/etc/dispatcher}"
: "${BACKUP_LOG_DIR:=/var/log/dispatcher}"

timestamp() { date -u +%Y%m%dT%H%M%SZ; }
