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

### Real-time resource / unit management (Stage 10)

An `app/resources/` module keeps the **live operational state** of every
dispatchable **unit** (отделение / расчёт), its **vehicle**, **crew** and
**personnel**: current status, crew composition, incident assignments,
per-vehicle condition (fuel, mileage, service) and an **append-only history** of
every change. It is built **on top of** the Stage-2 resource model without
modifying it — vehicles / personnel / stations stay the existing `resources`
rows, and the 9 minimum statuses (В боевом расчёте, Свободно, Следует к месту
вызова, Работает на месте, Возвращается, На обслуживании, На ремонте, Недоступно,
Резерв) are **catalog data** changeable without code. A status change here
propagates to `resources.availability_status`, so the **Dispatch Engine reads
current data without any engine change**. Coordinates come through a pluggable
`PositionProvider` (stored last-known position; **no GPS**). 9 operational tables,
native PG enums, reversible migration + status seed. REST under `/api/v1`:
`units`, `units/{id}` (`PATCH /status`, `/crew`, `/assign`, `/return`,
`/location`), `vehicles`, `vehicles/{id}/status`, `crews`, `crews/{id}/composition`,
`personnel`, `personnel/{id}/status`, `resources/bulk-status`, `resources/status`,
`resources/history`. No GPS, WebSocket, telemetry, external exchange or AI —
WebSocket-ready seams left for the next stage. See
[`docs/resources.md`](docs/resources.md).

### Call management (Stage 11)

An `app/calls/` module handles the **reception, registration and processing of
emergency calls**. Every incoming call becomes its own entity and is **linked to
one or more incident cards** (Stage 9) — it either creates a new incident or is
attached to an existing one, and that selection logic lives in a dedicated
`CallIncidentLinker` that reuses the Incident Management service **unchanged**. It
owns the call **lifecycle as a state machine** (new → ringing → accepted →
in-progress → linked → completed; cancellable; recoverable error), **rejecting
invalid transitions**, and a priority **dispatch queue** built for multiple
dispatcher workstations. Telephony is abstracted behind a pluggable
`CallProvider` interface (receive / answer / end / hold / transfer / health) with
a fully working **`MockCallProvider`** — real SIP / Asterisk / FreeSWITCH plugs in
without code change. Call **recordings** and **transcripts** are modelled as
metadata only (no audio, no ASR). 8 tables, native PG enums, reversible
migration, append-only history. REST under `/api/v1/calls`: create, list, get,
`PATCH /status`, `/incident` (create or link), `/queue`, `/history`, `/assign`,
telephony actions and `provider/health`. No real telephony, recording, speech
recognition or AI — seams left for the next (AI) stage. See
[`docs/calls.md`](docs/calls.md).

### AI Services platform (Stage 12)

An `app/ai/` module is a **platform** that unifies the system's intelligent
services — **transcription, entity extraction, incident classification,
summarisation and combined analysis** — behind one abstraction layer. Every
backend implements a single **`AIProvider`** interface (`transcribe` /
`extract_entities` / `classify_incident` / `summarize` / `analyze` /
`health_check`), so **replacing the AI model never touches business logic**; a
**registry** lets several providers be connected at once and selected per request
(OpenAI / Azure / local LLM / ASR). The only implementation now is a fully working
**`MockAIProvider`** (offline, deterministic Russian keyword/regex heuristics).
Each result carries its **confidence, model, model version and processing time**,
and every call is **audited** (metadata only — prompts and call text are never
stored). Integration is **read-only and advisory**: `CallAnalysisPipeline` reads a
call's transcript and returns a suggestion bundle; the AI **never** changes an
incident, dispatches units, edits rules or changes resource statuses — the
dispatcher always decides. REST under `/api/v1/ai`: `transcribe`, `extract`,
`classify`, `summarize`, `analyze`, `calls/{id}/analyze`, `providers`, `health`,
`audit`. See [`docs/ai.md`](docs/ai.md).

### Administration platform (Stage 13)

An `app/admin/` module is the single **administration platform** — managing
**users, roles and permissions (RBAC)**, system **settings**, **directories**
(catalogs), **integrations** and audit-log views. It **reuses** the Stage-2 RBAC
tables (`users` / `roles` / `permissions`) and the existing `audit_logs` trail
**unchanged**, adding 12 tables around them (permission groups, account statuses,
sessions, password policies, auth methods, versioned settings + history,
integrations + providers + configs + health checks). **RBAC** resolves a user's
permissions through roles (superuser bypass); passwords are PBKDF2-hashed and
validated against a configurable **password policy**; **settings** are typed,
categorised and **versioned with full history**; **directories** let catalogs be
edited as data without code; **integrations** never store secrets in clear text
(masked, referenced via a `secret_ref`); external auth (LDAP/AD/OIDC/SAML) is
represented but **not implemented** (no SSO/2FA). Every change is **audited**
(who / when / old → new / reason). REST under `/api/v1/admin`: `users`, `roles`,
`permissions`, `settings` (+ history), `directories`, `integrations` (+ health),
`audit`, `ai/providers`. Contains no dispatch logic and modifies no existing
business module. See [`docs/admin.md`](docs/admin.md).

### Observability platform (Stage 14)

An `app/observability/` module provides **monitoring, logging and observability**
for the whole system — real-time component state and diagnostics — **without a
new database table** and **without changing any business logic**. Every subsystem
exposes state through one **`HealthProvider`** interface (`health` / `readiness` /
`liveness` / `version`); the platform supplies a health **adapter** per module
(DB-, provider- or stateless-backed) so all modules are covered without editing
them. A backend-agnostic in-memory **metrics registry** (counters / gauges /
histograms) collects request rate, error %, API response time, uptime and business
gauges (active incidents / calls, available units, queue size, active users). A
**`LoggingService`** gives all six levels (TRACE…CRITICAL), structured output,
Trace-ID correlation and **masking** of secrets / personal data / conversation
text. Each request carries a unique **Trace ID** (via `contextvars`) that flows
through all services and stamps every log line. An **`AlertService`** evaluates
rules (service unavailable, error-rate/response-time/queue thresholds, health-check
failure) and **generates events** (no real delivery). REST under
`/api/v1/observability`: `health` (+ `live`/`ready`), `metrics` (+ Prometheus
text), `logs`, `traces`, `alerts`, `status`. Not tied to any product
(Prometheus/Grafana/OpenTelemetry/ELK); seams left for the next (analytics/KPI)
stage. See [`docs/observability.md`](docs/observability.md).

### Operational analytics platform (Stage 15)

An `app/analytics/` module is the **operational-intelligence** layer — **KPIs**,
role **dashboards**, **statistics**, **trends**, **decision-support findings**,
**reports** and **exports** — giving management and dispatchers objective
information about the service. It is **read-only** (consumes existing modules'
data through their public models, changes nothing, and never influences real-time
decisions — no Dispatch-Engine effect) and adds **no database table** (computed on
demand, briefly cached). KPIs live in an **extensible registry** (add a KPI without
touching existing code): call/incident counts, average registration/decision/
assignment times, dispatcher & unit load, resource utilization, and confirmed-
recommendation rate. Four role dashboards (shift lead, garrison chief, admin,
dispatcher) each expose their own KPI set. Reports are daily/weekly/monthly/custom;
a single **`ExportService`** renders CSV and **XLSX** (pure-stdlib OOXML writer —
no new dependency; PDF plugs in later) and **audits every export**. **RBAC** gates
reads/exports (reusing the Administration RBAC), and Decision Support surfaces
overloaded districts/units and load trends as advisory findings (**no AI, no
forecasting**). REST under `/api/v1/analytics`: `kpi`, `statistics`,
`dashboard/{role}`, `reports`, `trends`, `decision-support`, `export`. See
[`docs/analytics.md`](docs/analytics.md).

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
`get_settings()`. Secrets are resolved through the
[`app.config.secrets`](backend/app/config/secrets/) provider abstraction and are
never committed to the repository — see
[`docs/production/secrets.md`](docs/production/secrets.md).

## Production operation

Operational documentation for running the system in production lives in
[`docs/production/`](docs/production/) (index:
[`docs/production/README.md`](docs/production/README.md)). It covers
configuration & environments, secrets, backup & retention, disaster recovery,
scaling, containerization, CI/CD, migrations, performance/load testing, a
security audit, integrations readiness, and the developer/admin/dispatcher/
install/upgrade/maintenance guides. See also the
[readiness checklist](docs/readiness-checklist.md) and the
[final readiness report](docs/production-readiness-report.md).

Operational tooling:

- **`Makefile`** — platform-agnostic build/test/lint/migrate/container targets
  (`make help`).
- **`scripts/backup/`** — database/config/logs/uploads backup, restore, retention.
- **`scripts/verify/`** — migration verification (`check_migrations.sh`) and
  automated readiness checks (`verify_readiness.sh`).
- **`scripts/perf/loadtest.py`** — load/stress/soak/recovery harness.
- **`scripts/healthcheck.sh`** — liveness/readiness probe.
- **`.github/workflows/ci.yml`** — reference CI pipeline (lint, tests, migration
  checks, container build) over the same Makefile targets.
- **`deploy/env/*.example`** — per-environment configuration templates.

## Simulation & Training Platform

An **isolated** training contour ([`backend/app/simulator/`](backend/app/simulator/))
for training dispatchers, running exercises, replaying incidents and modelling
emergencies — with automatic evaluation of the trainee's actions. It uses **no
production database** and adds **no migration**: all simulation state is
in-memory and scenarios are stored separately (in-memory or JSON files), so the
live system is never affected. Modes: учебный / экзаменационный / свободное
моделирование / воспроизведение. REST API under `/api/v1/training`. See
[`docs/simulator.md`](docs/simulator.md).

## Digital Twin (strategic analysis)

An **isolated** digital-twin platform
([`backend/app/digital_twin/`](backend/app/digital_twin/)) for strategic
analysis and long-term planning: model infrastructure-development options
(open/close stations, depot repair, road changes, new objects, changed norms),
analyse **territory coverage**, **compare scenarios**, **forecast load** and
generate **analytical reports** (coverage/risk maps, impact assessment,
justification). It works **only on copies of the data** and adds **no
migration**, so the live system is never affected; it **compares and
recommends** but never changes anything automatically. REST API under
`/api/v1/digital-twin`. See [`docs/digital-twin.md`](docs/digital-twin.md).

## Mobile platform (Commander & Responder)

Two thin mobile apps over a backend BFF ([`backend/app/mobile/`](backend/app/mobile/)
+ client SDK in [`mobile/`](mobile/)): **Commander** (command staff) and
**Responder** (field units). All decisions are made **server-side** — the apps
carry no business logic. Includes a **vendor-neutral PushService**, **offline**
cache + idempotent sync, and secure token/session handling (hash-only storage,
idle auto-logout, remote revoke). The BFF reuses existing services via a provider
seam and adds **no migration**. REST API under `/api/v1/mobile`. See
[`docs/mobile.md`](docs/mobile.md).

## License

Proprietary — internal scaffold.
