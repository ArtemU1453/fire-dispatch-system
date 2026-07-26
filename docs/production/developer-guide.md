# Developer Guide (§12)

For engineers extending the AI Dispatcher МЧС backend. Covers architecture,
conventions, local workflow and how to add functionality without breaking the
production-readiness guarantees.

## Architecture

Clean/layered architecture — see [../architecture.md](../architecture.md) and the
per-module docs. Each domain module (`incidents`, `resources`, `calls`, `dispatch`,
`rules`, `routing`, `gis`, `search`, `ai`, `admin`, `observability`, `analytics`)
follows the same shape:

```
models/         SQLAlchemy entities + enums
repositories/   data access (no business logic in the API layer)
services/       business logic
schemas/        Pydantic request/response
api/            thin FastAPI routers (adapters)
interfaces/     provider abstractions (external seams)
```

Cross-cutting: `config` (settings + secrets), `core` (logging, exceptions),
`database` (async engine/session), `api/deps` (DI).

## Conventions

- **Async everywhere** — SQLAlchemy 2.x async; one session per request. Avoid
  lazy relationship access outside a session (`MissingGreenlet`); load explicitly.
- **Typed** — Pydantic v2 schemas at the edges; `Mapped[...]` models.
- **DI** — inject `Settings` and services; **never** read `os.environ` directly;
  resolve secrets via the secrets provider.
- **Errors** — raise `AppError` subclasses (`NotFoundError`, `ConflictError`,
  `ValidationError`); the global handler maps them to HTTP.
- **Providers** — external dependencies go behind an interface + factory with a
  mock/default, selected by config (telephony, GIS, tracking, AI, cache).
- **No secrets, no PII in logs** — the masking policy is enforced in
  Observability; keep sensitive field names in the mask list.

## Local workflow

```bash
python3.13 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt ruff
make lint          # ruff
make test          # full suite (PostgreSQL tests skip if no DB)
make migrate-check # migrations apply/round-trip/no-drift (needs a DB)
make check         # lint + test (pre-commit gate)
```

Ruff config is in `pyproject.toml`. PostgreSQL-backed tests connect via the
settings DSN and skip when no database is reachable.

## Adding a feature (checklist)

1. Model + migration — `alembic revision --autogenerate`; hand-verify native
   enums; run `make migrate-check` (no drift, round-trips).
2. Repository → service → schema → thin API router; wire into
   `app/api/v1/router.py`.
3. Tests: unit (no DB) + `test_service_pg.py` + `test_api_pg.py` (skip w/o PG).
4. Docs: update the module doc + README; add config to `.env.example` if any.
5. `make check` green; open a PR — CI runs lint, tests, migration checks and the
   image build.

## Production-readiness guardrails

- Keep the app **stateless** (state in PostgreSQL) so it scales horizontally (§5).
- Add configuration through `Settings` with safe defaults; secrets through the
  provider (never the repo).
- Don't break migration reversibility; prefer expand/contract for schema changes
  ([migrations.md](migrations.md)).
- Don't change Dispatch Engine / Rule Engine / AI Platform algorithms as a side
  effect of infrastructure work.

## Testing tiers

- **Unit** — pure logic, no DB.
- **Integration (`*_pg`)** — real PostgreSQL/PostGIS; exact values against seeds.
- **API (`*_pg`)** — endpoints via httpx ASGI transport, incl. RBAC and auditing.
