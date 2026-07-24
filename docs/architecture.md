# Architecture

The backend follows **Clean Architecture** with clearly separated, inward-pointing
dependencies. Outer layers depend on inner layers, never the reverse.

```
            ┌──────────────────────────────────────────────┐
  HTTP  ──▶ │  API layer (app/api)                         │  FastAPI routers,
            │   - endpoints (thin adapters)                │  dependency wiring
            │   - deps.py (Dependency Injection)           │
            ├──────────────────────────────────────────────┤
            │  Service layer (app/services)                │  application/business
            │   - orchestrates repositories & AI           │  logic (added later)
            ├──────────────────────────────────────────────┤
            │  Repository layer (app/repositories)         │  Repository Pattern,
            │   - AbstractRepository (interface)           │  persistence isolation
            │   - SqlAlchemyRepository (implementation)    │
            ├──────────────────────────────────────────────┤
            │  Data layer (app/models, app/database)       │  ORM models, engine,
            │   - Base, sessions, engine                   │  session/unit-of-work
            └──────────────────────────────────────────────┘

  Cross-cutting (used by all layers, depend on nothing domain-specific):
    app/config     — typed settings from .env
    app/core       — logging, exception hierarchy
    app/middleware — request context / access logging
    app/schemas    — Pydantic v2 API contracts
    app/ai         — AI provider abstraction (extension seam)
    app/utils      — generic helpers
```

## Design principles applied

| Principle              | Where / how                                                                 |
|------------------------|------------------------------------------------------------------------------|
| **SOLID – SRP**        | Endpoints only adapt HTTP; services hold logic; repositories only persist.  |
| **SOLID – OCP**        | New routes/models added via aggregation points without editing the factory. |
| **SOLID – DIP**        | Services depend on `AbstractRepository`/`AIProvider`, not implementations.   |
| **DRY**                | `TimestampMixin`, generic `SqlAlchemyRepository`, single settings source.    |
| **KISS**               | No premature abstractions; minimal, readable modules.                       |
| **Clean Architecture** | Layered packages with inward dependencies only.                             |
| **Repository Pattern** | `AbstractRepository` + `SqlAlchemyRepository`.                              |
| **Dependency Injection** | FastAPI `Depends` + `app/api/deps.py` factories; session provider.        |

## Extending the scaffold

Add a new domain feature without changing the architecture:

1. **Model** — add `app/models/<entity>.py`, import it in `app/models/__init__.py`.
2. **Migration** — `alembic revision --autogenerate -m "add <entity>"`.
3. **Repository** — subclass `SqlAlchemyRepository`, set `model`.
4. **Schema** — add Pydantic contracts in `app/schemas/<entity>.py`.
5. **Service** — add `app/services/<entity>.py` (subclass `BaseService`).
6. **Dependency** — add a provider in `app/api/deps.py`.
7. **Endpoint** — add `app/api/v1/endpoints/<entity>.py`, include it in `router.py`.

No existing file needs structural change — only additive edits at the
designated aggregation points.
