# Database Structure (§12)

Reference to the database schema of the AI Dispatcher МЧС system. The **detailed
model** — every table, column, relationship and enum — is maintained in
[../data-model.md](../data-model.md) and the entity diagram
[../er-diagram.puml](../er-diagram.puml); this page is the operational overview
and the conventions that apply across all tables.

## Engine

- **PostgreSQL 16** with the **PostGIS** extension (spatial columns/indexes).
- Managed exclusively through **Alembic** migrations ([migrations.md](migrations.md)).
- Access via SQLAlchemy 2.x async ORM (asyncpg); Alembic uses psycopg (sync).

## Domains (table groups)

| Domain | Purpose | Module doc |
|--------|---------|-----------|
| Reference/geo | administrative areas, organisations, incident/resource types | [../data-model.md](../data-model.md) |
| GIS | geocoding results, spatial reference data | [../gis.md](../gis.md) |
| Incidents | incidents, lifecycle, dispatches | [../incidents.md](../incidents.md) |
| Resources | units, vehicles, personnel, assignments, statuses | [../resources.md](../resources.md) |
| Calls | calls, queue, history, incident links | [../calls.md](../calls.md) |
| Dispatch | recommendation inputs/outputs | [../dispatch.md](../dispatch.md) |
| Rules | dispatch rules, conditions, versions | [../rules.md](../rules.md) |
| Routing | route/ETA reference (computed, largely non-persistent) | [../routing.md](../routing.md) |
| AI | AI analysis audit records | [../ai.md](../ai.md) |
| Admin/security | users, roles, permissions, settings (+history), integrations, `audit_logs` | [../admin.md](../admin.md) |

Analytics and Observability are **read-only / in-memory** and add **no tables**.

## Conventions

- **Primary keys** — UUIDs.
- **Timestamps** — `created_at` / `updated_at` on entities.
- **Soft delete** — `is_deleted` flag where applicable; queries filter it out.
- **Enums** — native PostgreSQL enum types (values serialised by name), created
  and dropped by migrations.
- **Spatial** — PostGIS geometry columns with GiST indexes for proximity search.
- **Foreign keys / uniqueness / NOT NULL** — enforced at the database for
  integrity ([migrations.md](migrations.md)).
- **Auditing** — administrative actions and analytics exports recorded in
  `audit_logs`.
- **Settings history** — configuration changes are versioned; secret-like values
  masked in history.

## Inspecting a live database

```bash
alembic current             # applied revision
alembic history --verbose   # migration chain
psql ... -c "\dt"           # tables
psql ... -c "\d+ <table>"   # columns, indexes, constraints
```

## Backup & restore

Schema + data are captured by `pg_dump` (custom format) with the revision
recorded; restore and PostGIS provisioning are covered in [backup.md](backup.md)
and [recovery.md](recovery.md).
