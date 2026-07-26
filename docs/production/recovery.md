# Disaster Recovery (§4)

Documented procedures for restoring the AI Dispatcher МЧС system after failure.
Each procedure lists the trigger, the steps, and the verification. Backups are
produced per [backup.md](backup.md).

## Objectives

| Metric | Target (production) |
|--------|---------------------|
| **RPO** (max data loss) | ≤ 15 min with WAL archiving; ≤ 24 h with nightly dump only |
| **RTO** (max downtime) | ≤ 1 h for a full database restore; ≤ 5 min for a stateless service restart |

The application layer is **stateless** (all state is in PostgreSQL and the
secrets manager), so most recovery is "restore the database, redeploy the
containers, point them at the database".

## Roles

- **On-call operator** — executes procedures, owns the incident.
- **DBA / infrastructure** — owns storage, WAL archive, network.
- **System owner (МЧС)** — decides on failover and communicates downtime.

---

## Procedure 1 — Database restore (data corruption / loss)

**Trigger:** database unavailable, corrupted, or bad data must be rolled back.

1. **Stop writers** — scale the API to zero (or enable maintenance mode) so no
   new writes race the restore.
2. **Select a backup** — newest good dump under `$BACKUP_DIR/database`; check its
   `*.revision` sidecar matches the application version you will run.
3. **Restore:**
   ```bash
   PGPASSWORD=... scripts/backup/restore_database.sh <dump> --create
   ```
   (`--create` provisions a clean database + PostGIS extension; omit it and set
   `CONFIRM=yes` to restore in place.)
4. **Roll forward (if WAL archiving is enabled)** — apply archived WAL up to the
   desired recovery target time for minimal data loss.
5. **Validate schema:** `alembic current` must equal the target revision; run
   `scripts/verify/check_migrations.sh`.
6. **Restart API**, run the smoke checklist, then restore normal traffic.

**Verify:** health endpoint green, a sample incident/call reads correctly, KPI
counts are plausible.

---

## Procedure 2 — Configuration recovery

**Trigger:** configuration lost or misapplied; a bad config rollout.

1. Restore the config tarball: `tar -xzf config_<ts>.tar.gz -C /etc`.
2. Re-fetch secrets from the secrets manager (they are **not** in the backup) —
   verify `SECRETS_PROVIDER` and the required keys resolve (see
   [secrets.md](secrets.md)).
3. Validate configuration loads: start one instance with
   `APP_ENV=<env>` and confirm it boots and `/health` is green.
4. Roll the good configuration to the rest of the fleet.

**Config is versioned** (Administration module keeps settings history); prefer
rolling back to a previous known-good version there when the issue is an
application setting rather than infrastructure config.

---

## Procedure 3 — Service / component restart

**Trigger:** a service is unhealthy (memory leak, wedged worker, failed
dependency) but data is intact.

1. Identify the unhealthy component via `/health` (aggregates per-module health
   providers) and metrics/logs (Observability module).
2. Restart the affected container(s). Because instances are stateless and
   idempotent on startup (migrations are a no-op when already applied), a
   rolling restart is safe and causes no data change.
3. If a **dependency** (database, GIS provider, telephony) is down, the affected
   subsystem degrades gracefully — routing falls back to the straight-line
   estimator, GIS/geocoding uses cache — restart is not required; recovery is
   automatic when the dependency returns.
4. Confirm health returns green and error-rate metrics normalise.

---

## Procedure 4 — Full-site / host loss

**Trigger:** the host or environment is lost entirely.

1. Provision a new host/cluster from the container images and
   `deploy/` manifests.
2. Provision PostgreSQL/PostGIS; restore per **Procedure 1**.
3. Wire the secrets manager (Procedure 2, step 2).
4. Deploy the API containers (see [containerization.md](containerization.md));
   migrations run automatically on start.
5. Run the readiness checklist end-to-end before returning to service.

---

## Recovery drill

Rehearse Procedure 1 on a scratch host at least quarterly and record actual RTO
achieved. A backup that has never been restored is not a proven backup — the
verification steps in [backup.md](backup.md) double as the drill.
