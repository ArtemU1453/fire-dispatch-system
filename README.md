# AI Dispatcher МЧС — Backend

Industrial project scaffold for the **AI Dispatcher МЧС** system: a FastAPI
backend built on Clean Architecture, ready to extend with domain logic without
architectural change.

> This repository is a **scaffold**. It wires up configuration, database access,
> migrations, logging, containerisation and API documentation, plus a single
> `GET /health` endpoint. **No business logic is implemented yet** — the layers
> and extension seams are in place for future features.

## Tech stack

| Concern         | Technology            |
|-----------------|-----------------------|
| Language        | Python 3.13           |
| Web framework   | FastAPI               |
| ORM             | SQLAlchemy 2.x (async)|
| Migrations      | Alembic               |
| Database        | PostgreSQL            |
| Validation      | Pydantic v2           |
| ASGI server     | Uvicorn               |
| Testing         | pytest                |
| Containerisation| Docker & Docker Compose |

## Project structure

```
fire-dispatch-system/
├── backend/
│   └── app/
│       ├── api/            # HTTP layer: routers, endpoints, DI wiring
│       │   ├── deps.py             # Dependency-injection providers
│       │   └── v1/
│       │       ├── router.py       # Aggregate v1 router
│       │       └── endpoints/
│       │           └── health.py   # GET /health
│       ├── core/           # Cross-cutting: logging, exception hierarchy
│       ├── database/       # Declarative Base, async engine, session factory
│       ├── models/         # SQLAlchemy ORM models (+ reusable base)
│       ├── repositories/   # Repository Pattern (abstract + SQLAlchemy impl)
│       ├── schemas/        # Pydantic v2 request/response contracts
│       ├── services/       # Application/business logic (orchestration)
│       ├── ai/             # AI provider abstraction (extension seam)
│       ├── utils/          # Generic helpers
│       ├── middleware/     # Request-context / access-logging middleware
│       ├── config/         # Typed settings loaded from .env
│       └── main.py         # App factory + ASGI entry point
├── migrations/             # Alembic environment & versioned migrations
├── tests/                  # pytest suite (hermetic, in-memory DB)
├── docs/                   # Architecture documentation
├── alembic.ini             # Alembic configuration
├── requirements.txt        # Pinned dependencies
├── pyproject.toml          # pytest / tooling configuration
├── Dockerfile              # Multi-stage backend image
├── docker-compose.yml      # Local stack: PostgreSQL + API
├── .env.example            # Sample environment configuration
└── README.md
```

See [`docs/architecture.md`](docs/architecture.md) for the layer diagram and the
step-by-step guide to adding a new feature.

## Quick start with Docker Compose (recommended)

Requires Docker and Docker Compose.

```bash
# 1. Create your environment file (use "db" as the DB host — see note below).
cp .env.example .env

# 2. Build and start PostgreSQL + the API (migrations run automatically).
docker compose up --build
```

> **Note:** inside Compose the API reaches PostgreSQL at host `db`. The Compose
> file already sets `POSTGRES_HOST=db` for the API container, so the value in
> `.env` is only used for host-side tooling.

The API is then available at:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- OpenAPI schema: <http://localhost:8000/openapi.json>
- Health check: <http://localhost:8000/health>

Verify:

```bash
curl http://localhost:8000/health
# {"status":"ok","app":"AI Dispatcher МЧС","version":"0.1.0",
#  "environment":"local","database":"up"}
```

## Local development (without Docker)

Requires Python 3.13 and a reachable PostgreSQL instance.

```bash
# 1. Create and activate a virtual environment.
python3.13 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies.
pip install -r requirements.txt

# 3. Configure environment (set POSTGRES_HOST=localhost etc.).
cp .env.example .env

# 4. Apply database migrations.
alembic upgrade head

# 5. Run the API (module path resolves because app lives under ./backend).
PYTHONPATH=backend uvicorn app.main:app --reload
```

## Database migrations (Alembic)

```bash
# Autogenerate a migration after adding/changing ORM models.
PYTHONPATH=backend alembic revision --autogenerate -m "describe change"

# Apply all pending migrations.
PYTHONPATH=backend alembic upgrade head

# Roll back the most recent migration.
PYTHONPATH=backend alembic downgrade -1
```

The database URL is injected into Alembic from application settings
(`migrations/env.py`), so there is a single source of configuration truth.

## Running the tests

The suite is hermetic — it uses an in-memory SQLite database and requires no
running PostgreSQL:

```bash
pip install -r requirements.txt
pytest
```

## Configuration

All settings are read from environment variables / `.env` and validated at
startup by `app/config/settings.py`. See [`.env.example`](.env.example) for the
full list. Nothing in the code reads `os.environ` directly — always go through
`get_settings()`.

## License

Proprietary — internal scaffold.
