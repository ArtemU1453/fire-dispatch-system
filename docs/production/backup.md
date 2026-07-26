# Backup & Retention (§3)

This document describes how the AI Dispatcher МЧС system is backed up and how
long backups are kept. It covers **what** is backed up, **how**, the
**retention** policy, and how to **verify** a backup. Restore/recovery
procedures are in [recovery.md](recovery.md).

> Backups never contain secrets. Passwords, API keys, tokens, certificates and
> encryption keys live in the secrets manager (see
> [secrets.md](secrets.md)); the file-backup script explicitly excludes
> `.env`, `*.key` and `*.pem`.

## What is backed up

| Asset | Source | Tool | Script |
|-------|--------|------|--------|
| **Database** (schema + data, incl. PostGIS geometry) | PostgreSQL | `pg_dump --format=custom` | `scripts/backup/backup_database.sh` |
| **Configuration** | `$BACKUP_CONFIG_DIR` (e.g. `/etc/dispatcher`) | `tar` | `scripts/backup/backup_files.sh` |
| **Logs** | `$BACKUP_LOG_DIR` (e.g. `/var/log/dispatcher`) | `tar` | `scripts/backup/backup_files.sh` |
| **Uploaded files** | `$BACKUP_UPLOADS_DIR` | `tar` | `scripts/backup/backup_files.sh` |

The database dump uses PostgreSQL **custom format** (compressed, selective
restore), and a sidecar `*.revision` file records the Alembic migration revision
the dump was taken at, so a restore can be validated against schema version.

## How to run

All parameters come from the environment (same variables the application uses);
the database password is supplied via `PGPASSWORD`, sourced from the secrets
manager — never from a committed file.

```bash
# Nightly full backup (database + config + logs + uploads + prune)
export POSTGRES_HOST=... POSTGRES_USER=... POSTGRES_DB=...
export PGPASSWORD="$(dispatcher-secret get POSTGRES_PASSWORD)"   # secrets manager
export BACKUP_DIR=/var/backups/dispatcher
scripts/backup/backup_all.sh
```

Schedule it with any scheduler (cron, systemd timer, Kubernetes CronJob). Example
cron entry (03:15 UTC daily):

```cron
15 3 * * *  PGPASSWORD_FILE=/run/secrets/pg /usr/local/bin/dispatcher-backup
```

## Retention policy

| Environment | Frequency | On-site retention | Off-site copy |
|-------------|-----------|-------------------|---------------|
| Production  | Daily full + continuous WAL (recommended) | 30 days (`BACKUP_RETENTION_DAYS`) | Weekly, ≥ 90 days |
| Staging     | Daily full | 14 days | — |
| Testing     | On demand | 7 days | — |

`scripts/backup/prune_backups.sh` enforces `BACKUP_RETENTION_DAYS` by deleting
dumps/tarballs older than the threshold. Adjust per environment via the env var.

**Point-in-time recovery (recommended for production):** in addition to nightly
`pg_dump`, enable PostgreSQL WAL archiving (`archive_mode=on`, `archive_command`
shipping WAL to durable storage). This bounds data loss to the WAL-shipping
interval (RPO) rather than 24h. The dump provides a known-good base backup; WAL
provides roll-forward. WAL archiving is an operator/database configuration and
is intentionally out of the application repository.

## Verifying a backup

A backup is only real if it restores. Periodically (monthly recommended):

1. Restore the latest dump into a scratch database
   (`scripts/backup/restore_database.sh <dump> --create` against a test host).
2. Run `alembic current` and compare to the dump's `*.revision` sidecar.
3. Run `scripts/verify/check_migrations.sh` (see §8) to confirm schema integrity.
4. Run the smoke checklist in [../readiness-checklist.md](../readiness-checklist.md).

## Off-site / durability

The scripts write to `$BACKUP_DIR`. In production, `$BACKUP_DIR` should be a
mount backed by durable, off-host storage (object storage, NAS, or a managed
snapshot service). Encryption at rest for the backup target is an
infrastructure responsibility; dumps may additionally be encrypted with an
operator-held key before leaving the host.
