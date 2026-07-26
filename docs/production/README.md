# Production Operation — Documentation Index

Operational documentation for running the AI Dispatcher МЧС system in production
(Stage 16). It complements the architecture and per-module documentation in
[`docs/`](../) and does not change any business logic — it prepares the system for
industrial operation.

## Contents

| Area | Document | Spec |
|------|----------|------|
| Configuration & environments | [configuration.md](configuration.md) | §1 |
| Secrets management | [secrets.md](secrets.md) | §2 |
| Backup & retention | [backup.md](backup.md) | §3 |
| Disaster recovery | [recovery.md](recovery.md) | §4 |
| Scaling architecture | [scaling.md](scaling.md) | §5 |
| Containerization | [containerization.md](containerization.md) | §6 |
| CI/CD | [cicd.md](cicd.md) | §7 |
| Database migrations | [migrations.md](migrations.md) | §8 |
| Performance & load testing | [performance.md](performance.md) | §9 |
| Security audit + risk register | [security-audit.md](security-audit.md) | §10 |
| External integrations readiness | [integrations-readiness.md](integrations-readiness.md) | §11 |
| Installation guide | [install.md](install.md) | §12 |
| Upgrade guide | [upgrade.md](upgrade.md) | §12 |
| Maintenance & operations | [maintenance.md](maintenance.md) | §12 |
| Administrator guide | [admin-guide.md](admin-guide.md) | §12 |
| Developer guide | [developer-guide.md](developer-guide.md) | §12 |
| Dispatcher guide | [dispatcher-guide.md](dispatcher-guide.md) | §12 |
| API reference | [api.md](api.md) | §12 |
| Database structure | [db-schema.md](db-schema.md) | §12 |
| **Readiness checklist** | [../readiness-checklist.md](../readiness-checklist.md) | §13 |
| **Final readiness report** | [../production-readiness-report.md](../production-readiness-report.md) | §14 |

## Architecture & modules

- System architecture: [../architecture.md](../architecture.md)
- Data model + ER diagram: [../data-model.md](../data-model.md),
  [../er-diagram.puml](../er-diagram.puml)
- Per-module docs: incidents, resources, calls, dispatch, rules, routing, gis,
  search, ai, admin, observability, analytics (in [`docs/`](../)).

## Tooling

- `Makefile` — platform-agnostic build/test/lint/migrate/container targets.
- `scripts/backup/` — database/config/logs/uploads backup, restore, retention.
- `scripts/verify/` — migration verification, readiness checks.
- `scripts/perf/loadtest.py` — load/stress/soak/recovery harness.
- `scripts/healthcheck.sh` — liveness/readiness probe.
- `.github/workflows/ci.yml` — reference CI pipeline (platform-agnostic underneath).
- `deploy/env/*.example` — per-environment configuration templates.
