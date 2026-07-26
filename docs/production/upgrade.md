# Upgrade Guide (§12)

How to upgrade a running deployment to a new version safely, and how to roll
back. The application is **stateless**, so upgrades are image swaps plus (when
present) a database migration.

## Before you upgrade

1. **Read the release notes** for breaking changes and required migrations.
2. **Back up the database** ([backup.md](backup.md)) — the dump records its
   revision for restore validation.
3. **Verify staging** — deploy the new version to staging, run
   `make migrate-check` and the test/load suites.

## Standard upgrade (zero-downtime)

1. **Publish** the new image tag.
2. **Migrate** the database as a one-shot job:
   ```bash
   alembic upgrade head
   ```
   Migrations are additive/expand-contract where possible ([migrations.md](migrations.md)),
   so running instances of the old version keep working during the roll.
3. **Roll** the API replicas to the new image (rolling update). Instances are
   stateless; each new instance no-ops on already-applied migrations.
4. **Gate** the rollout on the readiness probe (`/health`, `database=up`).
5. **Verify** — health green, smoke checks, error-rate/latency metrics normal.

For schema changes that cannot be made backward-compatible in one step, use the
**expand → deploy → contract** sequence in [migrations.md](migrations.md) across
two releases to preserve zero-downtime.

## Rollback

- **Code only** (no schema change, or schema still compatible): redeploy the
  previous image tag — instant, stateless.
- **Schema changed:** prefer restoring the pre-upgrade backup and rolling forward
  ([recovery.md](recovery.md)); `alembic downgrade <rev>` is available but may lose
  writes made under the new schema, so use it only when no such writes occurred.

## Dependency / base-image upgrades

- Bump pins in `requirements.txt`; CI (`make ci`) must stay green.
- Rebuild the image; the multi-stage Dockerfile re-resolves dependencies.
- Re-run `make migrate-check` and the full suite before promoting.

## Configuration changes

New settings ship with safe defaults ([configuration.md](configuration.md)).
Review the release notes for any new **required** variable or secret and provide
it (via config / secrets manager) before the roll.
