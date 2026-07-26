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
| Database        | PostgreSQL + PostGIS  |
| Geospatial      | GeoAlchemy2 / PostGIS |
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
step-by-step guide to adding a new feature, and
[`docs/data-model.md`](docs/data-model.md) for the full data model (ER diagram,
every table and relationship, normalization notes, and the indexing / scaling
strategy). A PlantUML diagram is provided in
[`docs/er-diagram.puml`](docs/er-diagram.puml).

### Data model (Stage 2)

The domain model is **resource-centric**: every managed object (station,
vehicle, hydrant, hospital, …) is a `Resource` typed by a catalog `ResourceType`,
so new kinds of resource are added as **data, not schema**. Vehicles, personnel,
equipment and stations have 1:1 specialization tables; geospatial data uses
PostGIS `geometry(Point/MultiPolygon, 4326)` columns with GiST indexes. All
tables carry `id` (UUID), `created_at`, `updated_at` and `is_deleted`
(soft-delete). See the data-model doc for details.

### GIS geospatial core (Stage 3)

An independent `app/gis/` module adds **geocoding, reverse geocoding, address
normalization, a geographic gazetteer and PostGIS spatial queries**. Geocoding
runs through a pluggable `GeoProvider` (Nominatim / Photon / Pelias / ArcGIS, and
an offline Fake provider), swappable via `GIS_PROVIDER`. REST endpoints under
`/api/v1`: `geocode`, `reverse-geocode`, `coordinates`, `validate-address`,
`normalize-address`, plus `spatial/*` (distance, radius, bbox, polygon, area).
Results are cached (Redis-ready interface) and every request is logged. See
[`docs/gis.md`](docs/gis.md).

### Universal resource search (Stage 4)

An `app/search/` module provides one **universal Search Engine** over the core
`Resource` entity — it finds any resource kind (station, vehicle, hydrant,
hospital, police, …) with the same algorithm; the type is just a filter.
Combinable filters (type, group/category, organization, availability, capability,
station, vehicle/equipment type, working status, text/address), PostGIS spatial
ops (`ST_DWithin`, KNN nearest, `ST_Within`, bbox), sorting, pagination and
result caching. REST endpoints under `/api/v1`: `resources/search`,
`resources/nearest`, `resources/radius`, `resources/filter`, `resources/{id}`.
A `SelectionStrategy` seam leaves it ready for the next stage (automatic unit
selection) with no engine changes. See [`docs/search.md`](docs/search.md).

### Dispatch Engine (Stage 5)

The `app/dispatch/` module forms a **recommended composition of forces and
equipment** for an incident (type + complexity + address/coordinates + dispatcher
constraints) — the decision-support core. It geocodes the incident, gets the
**active rules from the database Rule Engine**, consolidates the required
capabilities and minimum/recommended/reserve composition, searches candidates via
the Stage-4 Search Engine, **excludes** unavailable / out-of-zone / capability-
lacking resources (each with a logged reason), **scores** the rest (distance,
readiness, capability match, and an ETA seam for later), selects primary +
reserve **by capability, not by unit name**, checks sufficiency, and returns a
**confidence** and an **automatic explanation** for every choice. Recommendations,
their coverage, the resource-match log and the decision audit are **persisted**.
It is **advisory only** — it never dispatches, routes, computes ETA or uses AI.
REST: `POST /dispatch/recommend`, `POST /dispatch/preview`,
`GET /dispatch/{incident_id}`, `GET /dispatch/history/{incident_id}`. See
[`docs/dispatch.md`](docs/dispatch.md).

### Rule infrastructure (Stage 6)

An `app/rules/` module stores dispatch norms **in the database, versioned** —
never in code. Rules are grouped in categories/sets, scoped to incident types and
complexity, carry **conditions** (applicability), **actions** (prescriptions) and
structured **resource / capability requirements** described *by category and
capability, never by concrete units*. A single **Rule Engine / `RuleService`**
finds rules, evaluates their conditions, decides which apply and returns
ready-made **minimum / recommended / reserve composition** and required
capabilities. Every change creates a new **immutable published version** (exactly
one active per rule, enforced by a partial unique index); all versions are kept
and every lifecycle event is audited. It makes **no dispatch decision and selects
no resource** — it is the norm store the next stage's algorithm reads from. REST
under `/api/v1/rules` (list, get, by incident type, by category, versions,
requirements, create, update, delete). See [`docs/rules.md`](docs/rules.md).

### Routing & ETA (Stage 7)

An independent `app/routing/` module builds routes, computes travel distance and
estimates **time of arrival** between two points behind a single
**`RoutingProvider`** interface — so any backend (OSRM now; GraphHopper, Valhalla,
OpenRouteService or a commercial API later) plugs in through configuration. Ships
a dependency-free straight-line estimator (the default, works with no external
server), an **OSRM** HTTP provider, and a **fallback chain** that keeps working
when a backend is down. `RouteService` builds routes/geometry/waypoints;
`ETAService` (ETA only) is the entry point the Dispatch Engine will use via its
ETA seam — **without modifying the Dispatch Engine**. Route reuse is cached
in-memory (Redis-ready, no Redis yet). No traffic, closures, AI or auto-dispatch.
REST under `/api/v1/routing` (`GET /route`, `POST /eta`, `POST /distance`,
`GET /health`); provider outages return a clear 503. See
[`docs/routing.md`](docs/routing.md).

### Dispatcher workstation (Stage 8 · frontend)

A React + TypeScript + Vite single-page app (`frontend/`) — the **dispatcher's
workstation** and a **pure client** of the backend (no business logic on the
client; the backend is used unchanged). A dispatcher can sign in, create a call
card, enter an address (geocoded via GIS), see the incident on an interactive
**Leaflet** map, get **recommendations**, view the **route** and **ETA**, pick
units and confirm the composition. Built with Material UI, TanStack React Query
(server state), Zustand (UI state), React Router and Axios; a bottom status bar
shows the health of every backend engine. Client-side auth with an **RBAC-ready**
role model, normalized error handling, code-splitting/lazy-loading, memoization
and list virtualization. Tests with Vitest + React Testing Library. See
[`docs/frontend.md`](docs/frontend.md) — run with `cd frontend && npm install &&
npm run dev`.

### Incident management (Stage 9)

An `app/incidents/` module makes the **incident card the central entity** of the
system — every subsystem relates to an incident. It owns the incident **lifecycle
as a finite state machine** (created → checking → confirmed → selecting →
dispatch-confirmed → dispatched → on-scene → localized → liquidated → completed →
archived; cancellable before dispatch), **rejecting invalid transitions**. Every
change is recorded three ways: a human-facing **timeline** (chronology), a
field-level **history** (who / when / old → new / source) and a technical **log**.
It stores comments, attachment **metadata** (architecture only), participants and
locations, and links to **recommendations** (via the existing Dispatch Engine,
unchanged) and **dispatched units** (resources). 10 tables, native PG enums,
reversible migration. REST under `/api/v1/incidents` (create, list,
active/archive, get, update, `PATCH /status`, `/timeline`, `/comments`, `/units`,
`/recommend`). No telephony, speech, AI, admin panel or external exchange — seams
left for the next stage. See [`docs/incidents.md`](docs/incidents.md).

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

Requires Python 3.13 and a reachable **PostgreSQL instance with the PostGIS
extension available** (the first migration runs `CREATE EXTENSION postgis`, so
the database role must be allowed to create it, or an admin should enable it
once). The Docker Compose stack already uses a PostGIS image.

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
