# Configuration (§1)

All configuration is **centralised** and **typed**. There is a single source of
truth — `app.config.settings.Settings` (Pydantic Settings) — and **nothing in
the code reads `os.environ` directly**; everything goes through `get_settings()`
(or the secrets provider for sensitive values). Every parameter has a default, is
validated at startup, and can be overridden per environment.

## Environments

`APP_ENV` selects the deployment tier: `local`, `dev`, `testing`, `staging`,
`production`. Templates:

| Tier | Template | Notes |
|------|----------|-------|
| Development | `.env.example` → `.env` | `DEBUG=true`, permissive CORS, local DB |
| Testing / CI | `deploy/env/testing.env.example` | throwaway creds, `GIS_PROVIDER=fake` |
| Staging | `deploy/env/staging.env.example` | production-like, secrets via files |
| Production | `deploy/env/production.env.example` | `DEBUG=false`, `LOG_JSON=true`, secrets via files/vault, locked-down CORS |

Copy a template, adjust, and provide it to the process (`.env`, container env,
ConfigMap). **Secrets are not in these files** in staging/production — see
[secrets.md](secrets.md).

## Precedence

Real environment variables override values in the `.env` file, which override
the built-in defaults. Unknown variables are ignored, so one `.env` can be shared
with other tooling.

## Parameter reference

### Application
| Variable | Default | Purpose |
|----------|---------|---------|
| `APP_NAME` | AI Dispatcher МЧС | display name |
| `APP_ENV` | local | environment tier |
| `APP_VERSION` | 0.1.0 | reported version (health/metrics) |
| `DEBUG` | false | verbose errors — **must be false in production** |
| `API_V1_PREFIX` | /api/v1 | versioned API mount |
| `HOST` / `PORT` | 0.0.0.0 / 8000 | bind address |

### Logging
| `LOG_LEVEL` | INFO | DEBUG…CRITICAL |
| `LOG_JSON` | false | structured JSON logs (set true for aggregation) |

### Secrets
| `SECRETS_PROVIDER` | env | `env` / `file` / `vault` |
| `SECRETS_DIR` | /run/secrets | file provider directory |
| `SECRETS_ENV_PREFIX` | (empty) | env provider key prefix |
| `VAULT_*` | — | corporate secrets-manager seam |

### Database & engine
| `POSTGRES_HOST/PORT/USER/DB` | localhost/5432/dispatcher/dispatcher | connection |
| `POSTGRES_PASSWORD` | — | **secret** (via secrets provider in prod) |
| `DB_ECHO` | false | log SQL |
| `DB_POOL_SIZE` / `DB_MAX_OVERFLOW` | 5 / 10 | pool sizing (tune for load, §9) |
| `DB_POOL_PRE_PING` | true | validate connections before use |

The async DSN (`SQLALCHEMY_DATABASE_URI`, asyncpg) and sync DSN
(`SQLALCHEMY_DATABASE_URI_SYNC`, psycopg for Alembic) are **computed** from the
above — never set them directly.

### CORS
| `CORS_ORIGINS` | `["*"]` | JSON array; **restrict in production** to real origins |

### GIS / geocoding, Search, Routing
Provider selection, endpoints, timeouts and cache backends
(`GIS_*`, `SEARCH_*`, `ROUTING_*`). Cache backends are `memory`/`none` today with
a Redis-ready seam (`GIS_REDIS_URL`) for multi-instance sharing (§5). Full list
and defaults are documented inline in `.env.example` and `Settings`.

## Externalised rules

Dispatch rules are configuration, not code: `DISPATCH_RULES_PATH` points at a
YAML file; empty uses the bundled `default_rules.yaml`. Rules can also be managed
via the Administration module. This keeps operational policy out of source code.

## Adding a parameter (for developers)

1. Add a typed field with a default to `Settings`.
2. Document it in `.env.example`.
3. Read it via the injected `Settings` — never `os.environ`.
4. If it is sensitive, resolve it through the secrets provider instead and add it
   to the secret inventory in [secrets.md](secrets.md).
