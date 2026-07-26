# CI/CD (§7)

The delivery pipeline is defined as a set of **platform-agnostic commands** (the
`Makefile` and `scripts/`), with a **reference** GitHub Actions workflow that
merely calls them. Porting to another CI/CD product (GitLab CI, Jenkins,
TeamCity, Azure DevOps) means invoking the same commands — no rewrite of logic.

> Constraint honoured: the architecture is **not** tied to a specific CI/CD
> platform. The workflow file is an example, not a dependency.

## Pipeline stages

| Stage | Command | What it proves |
|-------|---------|----------------|
| **Build (deps)** | `make install` | dependencies resolve |
| **Static analysis** | `make lint` (`ruff check`) | style/lint/quality gate |
| **Automated tests** | `make test` (`pytest`) | unit + integration + API suite green |
| **Migration checks** | `make migrate-check` | migrations apply, match models, roll back, round-trip (§8) |
| **Container build** | `make build-image` | image builds reproducibly |

`make ci` chains install → lint → test → migrate-check for a single local gate
identical to what the pipeline runs.

## Reference workflow

`.github/workflows/ci.yml` implements three jobs:

1. **lint** — installs `ruff`, runs `ruff check backend tests`.
2. **test** — starts a `postgis/postgis:16-3.4` service, applies migrations,
   runs `scripts/verify/check_migrations.sh` (round-trip + drift), then the full
   `pytest` suite against real PostgreSQL/PostGIS.
3. **container** — `docker build` of the backend image.

Triggers: pull requests, pushes to `main`, and manual dispatch.

### Quality gates

- **Lint must pass** (`ruff`, config in `pyproject.toml`).
- **All tests must pass**, including PostgreSQL-backed integration and API tests
  (they run for real in CI because a database service is provided; they skip
  only when no database is reachable, e.g. a laptop without PostgreSQL).
- **No migration drift** — `alembic check` fails the build if models and
  migrations diverge.
- **Image builds** — a broken Dockerfile fails the pipeline.

## Deployment (CD) outline

Deployment is environment-promotion, not part of this repository's automation,
but the building blocks are here:

1. On a tagged release, build and push the image
   (`docker build` → registry) with the version tag.
2. Run migrations as a one-shot job against the target database
   (`alembic upgrade head`) — safe and idempotent.
3. Roll out the new image (rolling update; instances are stateless, §5).
4. Gate the rollout on the readiness probe (`/health`, `database=up`).
5. Keep the previous image tag for instant rollback; database rollback uses the
   backup/recovery procedures ([recovery.md](recovery.md)).

## Secrets in CI/CD

CI uses **throwaway** credentials for its ephemeral test database only. Real
secrets are never in the repository or in workflow files — they are injected
from the CI system's secret store at deploy time and resolved at runtime through
the secrets provider ([secrets.md](secrets.md)).
