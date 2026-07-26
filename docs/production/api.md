# API Reference (§12)

The AI Dispatcher МЧС backend exposes a versioned REST API. This page is the
entry point; the **authoritative, always-current** reference is the
auto-generated OpenAPI document served by the running application.

## Live documentation

| Resource | Path |
|----------|------|
| Swagger UI | `/docs` |
| ReDoc | `/redoc` |
| OpenAPI JSON | `/openapi.json` |
| Health (unversioned, for probes) | `/health` |

All domain endpoints are mounted under `API_V1_PREFIX` (default `/api/v1`).

## Modules and routers

The versioned router aggregates all domains (order as wired in
`app/api/v1/router.py`):

| Prefix (under `/api/v1`) | Domain | Detail |
|--------------------------|--------|--------|
| `/health` | service health | this page |
| `/gis` | geocoding / spatial | [../gis.md](../gis.md) |
| `/resources` | units/vehicles/personnel | [../resources.md](../resources.md) |
| `/search` | cross-entity search | [../search.md](../search.md) |
| `/dispatch` | recommendations | [../dispatch.md](../dispatch.md) |
| `/rules` | dispatch rules | [../rules.md](../rules.md) |
| `/routing` | routes / ETA | [../routing.md](../routing.md) |
| `/incidents` | incident lifecycle | [../incidents.md](../incidents.md) |
| `/calls` | call management | [../calls.md](../calls.md) |
| `/ai` | AI analysis | [../ai.md](../ai.md) |
| `/admin` | users/roles/settings/integrations | [../admin.md](../admin.md) |
| `/observability` | health/metrics/logs | [../observability.md](../observability.md) |
| `/analytics` | KPIs/dashboards/reports/export | [../analytics.md](../analytics.md) |

## Conventions

- **Content type** — JSON request/response, validated by Pydantic v2 schemas.
- **Errors** — consistent `{"detail": "..."}`; status codes from the domain
  error hierarchy: `404` not found, `409` conflict, `422` validation, `403`
  authorization.
- **Correlation** — every response is traceable via the request Trace ID (in
  logs/metrics) from the Observability layer.
- **Versioning** — breaking changes go under a new prefix; the current version is
  `v1`.

## Security

- **RBAC** — permission-gated endpoints (e.g. analytics/admin). See the
  [security audit](security-audit.md) for the authentication prerequisite (R1)
  before external exposure.
- **CORS** — restrict `CORS_ORIGINS` to real dispatcher-workstation origins in
  production.
- **Rate limiting / TLS** — applied at the ingress (see security audit R4/R5).

## Using the API from clients

The frontend and any workstation client consume this API over HTTP; there is no
server affinity, so clients may talk to any instance behind the load balancer
(§5). Generate typed clients from `/openapi.json` if desired.
