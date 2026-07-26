# Installation Guide (§12)

How to install and run the AI Dispatcher МЧС backend from a clean environment.
Two paths: **containers** (recommended) and **bare-metal/venv** (development).

## Prerequisites

- **Docker + Docker Compose** (container path), or
- **Python 3.13** and **PostgreSQL 16 with the PostGIS extension** (bare-metal).
- Outbound access to the configured GIS provider (or use `GIS_PROVIDER=fake`).

## Option A — Docker Compose (recommended)

```bash
git clone <repo> && cd fire-dispatch-system
cp .env.example .env            # adjust; keep real secrets OUT of .env in prod
make run                        # docker compose up -d --build
```

- The `db` service is PostGIS-enabled PostgreSQL 16.
- The `api` service runs `alembic upgrade head` then starts Uvicorn.
- API: `http://localhost:8000` — OpenAPI docs at `/docs`, health at `/health`.
- Optional shared cache: `docker compose --profile cache up -d`.

Verify:
```bash
scripts/healthcheck.sh                    # liveness
READINESS=1 scripts/healthcheck.sh        # readiness (requires database=up)
```

Stop: `make stop`.

## Option B — Bare-metal / virtualenv (development)

```bash
python3.13 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

# Provision PostgreSQL + PostGIS and set connection env (or use .env):
export POSTGRES_HOST=localhost POSTGRES_USER=dispatcher \
       POSTGRES_PASSWORD=dispatcher POSTGRES_DB=dispatcher
psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
     -c "CREATE EXTENSION IF NOT EXISTS postgis;"

alembic upgrade head                       # create schema + seed data
uvicorn app.main:app --host 0.0.0.0 --port 8000   # from repo root (PYTHONPATH=backend)
```

## Production install (outline)

1. Build and publish the image (`make build-image TAG=<version>`; push to your
   registry).
2. Provision managed PostgreSQL 16 + PostGIS; create the database role.
3. Provide configuration via `deploy/env/production.env.example` (as ConfigMap /
   env) and **secrets via files or vault** (`SECRETS_PROVIDER=file`) —
   [secrets.md](secrets.md).
4. Run migrations once as a job (`alembic upgrade head`).
5. Deploy N stateless API replicas behind a load balancer; wire the readiness
   probe to `/health` (`database=up`). See [containerization.md](containerization.md)
   and [scaling.md](scaling.md).
6. Configure backups ([backup.md](backup.md)) and observability exporters.
7. Run the [readiness checklist](../readiness-checklist.md) before go-live.

## Post-install verification

- `GET /health` → `status: ok`, `database: up`.
- OpenAPI at `/docs` lists all module routers.
- `make migrate-check` passes (schema matches models, round-trips).
- `make test` passes against the target database.
