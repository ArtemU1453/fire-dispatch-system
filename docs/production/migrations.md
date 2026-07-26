# Database Migrations (§8)

How schema changes are managed, verified, rolled back, and how compatibility and
data integrity are guaranteed. Migrations are managed with **Alembic**; the
history lives in `migrations/versions/`.

## Principles

- **Single source of truth** — the SQLAlchemy models. Migrations are generated
  from them and hand-verified (native PostgreSQL enums are adjusted so
  autogenerate stays clean).
- **Forward-only in production, reversible in principle** — every migration
  implements `downgrade`, so a bad deploy can be rolled back; production prefers
  roll-forward + restore for data safety.
- **Idempotent apply** — `alembic upgrade head` against an already-migrated
  database is a no-op, so rolling restarts and multiple instances are safe (§5).

## Verification

`scripts/verify/check_migrations.sh` (run by `make migrate-check` and CI) proves
four properties against a real PostgreSQL/PostGIS database:

1. **Applies** — `alembic upgrade head` succeeds from an empty database.
2. **No drift** — `alembic check` finds no difference between the models and the
   migration history (autogenerate would produce nothing).
3. **Rolls back** — `alembic downgrade base` unwinds the entire chain cleanly.
4. **Round-trips** — `alembic upgrade head` re-applies after the downgrade.

Each historical migration was additionally verified for round-trip when it was
introduced (per-stage), so the whole chain is known to reverse.

## Running migrations

```bash
alembic upgrade head        # apply all           (make migrate)
alembic downgrade -1        # roll back one step   (make migrate-down)
alembic current             # show applied revision
alembic history --verbose   # full chain
```

In containers, migrations run automatically before the API starts (see the
Compose `command`); in Kubernetes, run them as a Job / initContainer before the
rollout.

## Schema compatibility & zero-downtime changes

To keep multiple running instances compatible during a rollout, follow the
**expand/contract** pattern:

1. **Expand** — additive change (new nullable column/table/index). Old and new
   code both work against it.
2. **Deploy** the new code that uses the new schema.
3. **Contract** — a later migration removes the now-unused old columns.

This avoids a window where a running old instance sees a schema it doesn't
understand. Backfills of large tables run as batched data migrations or
out-of-band jobs rather than blocking DDL.

## Data integrity

- **Constraints** — foreign keys, NOT NULL, uniqueness and enum types are
  enforced at the database, so migrations cannot leave orphaned or invalid rows.
- **Transactions** — each migration runs in a transaction; a failure rolls the
  whole step back, never leaving a half-applied schema.
- **PostGIS** — spatial columns and indexes are created/dropped by the
  migrations; the `postgis` extension is provisioned on restore
  ([recovery.md](recovery.md)).
- **Backups first** — take a database backup before applying migrations in
  production ([backup.md](backup.md)); the dump records the revision it was
  taken at for restore validation.

## Rollback procedure (production)

1. Stop the rollout; if the new code is incompatible, redeploy the previous
   image tag (instant, stateless).
2. If the schema must be reverted, `alembic downgrade <previous_revision>` — but
   prefer restoring from backup + roll-forward when data has changed, to avoid
   losing writes made under the new schema.
3. Verify with `alembic current` and the smoke checklist.
