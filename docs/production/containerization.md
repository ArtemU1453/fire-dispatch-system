# Containerization (§6)

The backend ships as a single OCI container image. This document covers the
image, how to run it, environment configuration, readiness checks, and how it is
prepared for orchestration (Kubernetes/Swarm) later.

## Image

`Dockerfile` is a **multi-stage** build:

- **builder** — installs Python dependencies into an isolated virtualenv
  (`/opt/venv`).
- **runtime** — `python:3.13-slim`, copies only the virtualenv and the app
  sources, runs as an **unprivileged** user (`appuser`, uid 1000), exposes
  `8000`, and declares a `HEALTHCHECK`.

Only `backend/`, `migrations/` and `alembic.ini` are copied — no tests, no
`.env`, no secrets. `.dockerignore` keeps the build context clean.

```bash
docker build -t dispatcher-api:0.1.0 .      # or: make build-image TAG=0.1.0
```

## Configuration (12-factor)

All configuration is supplied via environment variables — nothing is baked into
the image. The full list and defaults are in
[configuration.md](configuration.md); `.env.example` is the annotated template.
Key ones:

| Variable | Purpose |
|----------|---------|
| `APP_ENV` | `local`/`dev`/`testing`/`staging`/`production` |
| `POSTGRES_*` | database connection (password via secrets, not env, in prod) |
| `SECRETS_PROVIDER` | `env`/`file`/`vault` — where secrets come from |
| `LOG_JSON` | structured logs for aggregation |
| `CORS_ORIGINS` | allowed dispatcher-workstation origins |

**Secrets are never passed as plain env in production.** Set
`SECRETS_PROVIDER=file` and mount them at `/run/secrets` (Docker/K8s secrets),
or use the vault seam. See [secrets.md](secrets.md).

## Readiness check

The image declares:

```dockerfile
HEALTHCHECK CMD python -c "... urlopen('http://127.0.0.1:8000/health') ..."
```

- **Liveness** — the probe returns 0 when the process serves `/health` (HTTP
  200). Docker/Swarm/Compose use it to restart a wedged instance.
- **Readiness** — `/health` also reports `database: up|down` in its body. For
  Kubernetes, use a readiness probe that requires `database=up` (the helper
  `scripts/healthcheck.sh` with `READINESS=1` does exactly this) so traffic is
  only routed to instances whose database is reachable.

Compose mirrors the image healthcheck and gates the API on the database's
health (`depends_on: condition: service_healthy`).

## Running

### Single host (Docker Compose)

```bash
cp .env.example .env        # adjust values; keep real secrets out of it
make run                    # docker compose up -d --build
# API on http://localhost:8000 ; migrations run automatically on start
make stop
```

Optional shared cache for multiple instances:
`docker compose --profile cache up -d`.

### Standalone container

```bash
docker run --rm -p 8000:8000 \
  -e POSTGRES_HOST=db -e POSTGRES_DB=dispatcher \
  -e POSTGRES_USER=dispatcher \
  --mount type=bind,src=/run/secrets,dst=/run/secrets,ro \
  -e SECRETS_PROVIDER=file \
  dispatcher-api:0.1.0
```

The container runs `alembic upgrade head` (via Compose command) or you run it as
an init step; instances started against an already-migrated database no-op, so
a rolling restart is safe.

## Orchestration readiness (Kubernetes / Swarm)

The image is orchestrator-ready without change:

- **Stateless** — safe to run N replicas behind a Service/load balancer (§5).
- **Config via env + mounted secrets** — maps directly to ConfigMap + Secret.
- **Health endpoint** — maps to `livenessProbe` (200) and `readinessProbe`
  (`database=up`).
- **Migrations** — run as a Job / initContainer before rolling out new pods.
- **Non-root, single port** — satisfies common Pod security policies.

Manifests are intentionally not committed in this stage (no cluster is
provisioned); the properties above are the deliverable. See
[scaling.md](scaling.md) for the target topology.
