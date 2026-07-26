# Scaling Architecture (§5)

This describes how the AI Dispatcher МЧС system scales **horizontally** to serve
multiple dispatcher workstations, multiple backend instances and multiple
dispatch centres. Per the stage constraint, **clustering is not implemented
here** — this is the prepared architecture and the properties the code already
satisfies that make it possible.

## Design property: stateless backend

Each backend instance is **stateless**. All durable state is in PostgreSQL; the
only in-process state is caches (GIS/geocoding, search, routing) and the
Observability ring buffers, all of which are:

- **derived** (safe to lose — repopulated on demand), and
- **per-instance** (no cross-instance coordination required for correctness).

Because of this, N identical instances behind a load balancer are correct with
no code change. Nothing in a request depends on being routed to a particular
instance (no sticky sessions required).

```
                         ┌─────────────────────────────┐
   Dispatcher WS 1 ─┐    │        Load balancer         │
   Dispatcher WS 2 ─┼──▶ │  (round-robin, health-aware) │
   Dispatcher WS N ─┘    └───────┬───────────┬──────────┘
                                 │           │
                          ┌──────▼───┐  ┌────▼─────┐   (identical, stateless)
                          │  API #1  │  │  API #2  │ … │  API #M │
                          └────┬─────┘  └────┬─────┘   └────┬────┘
                               └──────┬──────┴──────────────┘
                                      ▼
                        ┌──────────────────────────────┐
                        │  PostgreSQL 16 + PostGIS      │
                        │  (primary + read replicas)    │
                        └──────────────────────────────┘
```

## What scales, and how

| Dimension | Mechanism | Status |
|-----------|-----------|--------|
| **Multiple backend instances** | Stateless API behind a load balancer; `/health` used for health-aware routing | Ready (run `--replicas N`) |
| **Multiple dispatcher workstations** | Thin clients over REST; no server affinity; concurrency handled at the DB | Ready |
| **Read-heavy load** (search, analytics, dashboards) | PostgreSQL **read replicas**; analytics/search are read-only aggregates | Seam prepared (see below) |
| **Multiple dispatch centres** | Per-centre scoping key on domain rows + centre-aware queries | Data model supports scoping; multi-tenant routing is a deployment choice |
| **Shared cache / rate limits across instances** | Redis-backed cache backend | Config seam present (`*_CACHE_BACKEND`, `GIS_REDIS_URL`); not wired |
| **Background/async work** (exports, scheduled reports) | External task queue (Celery/RQ/Arq) | Service seams present; no task backend bound |

### Read replicas

The engine is created from `SQLALCHEMY_DATABASE_URI` (a single primary today).
To use replicas, introduce a read-only engine/session bound to a replica DSN and
route read-only services (search, analytics, dashboards — all already read-only)
to it. No business logic changes; only the session dependency changes. This is
left as a deployment seam.

### Shared cache (Redis)

Caches are behind a backend selector (`memory` today). The settings already
expose `GIS_CACHE_BACKEND`/`SEARCH_CACHE_BACKEND`/`ROUTING_CACHE_BACKEND` and
`GIS_REDIS_URL`. A Redis backend implementing the same cache interface makes the
cache **shared** across instances (better hit-rate, and a place for distributed
rate-limiting) without touching call sites.

### Concurrency & consistency

- Writes are transactional (SQLAlchemy async sessions, one per request).
- Dispatch recommendation and assignment are guarded at the database level;
  optimistic-concurrency / row-level locking is the mechanism to prevent
  double-assignment when several dispatchers act at once. The single source of
  truth is the database, so horizontal scale-out does not weaken this guarantee.
- Migrations are safe to run once before a rollout; instances started against an
  already-migrated database no-op.

## Multiple dispatch centres

The domain model carries the organisational structure needed to scope data by
centre/garrison. Two deployment topologies are supported by the architecture:

1. **Shared deployment, logical scoping** — one backend + database serving many
   centres, queries scoped by centre. Cheapest; requires RBAC + query scoping
   (RBAC exists; per-centre scoping is a query concern, no schema change).
2. **Independent deployments** — one stack per centre, federated only for
   cross-centre reporting. Highest isolation; uses the same images/manifests.

Choosing between them is an operational decision; the code supports either.

## Explicitly out of scope (per constraint)

No clustering, service mesh, leader election, sharding or autoscaling controller
is implemented in this stage. Dispatch Engine, Rule Engine and AI Platform
algorithms are unchanged. This document and the configuration seams are the
deliverable; turning them on is future operational work.
