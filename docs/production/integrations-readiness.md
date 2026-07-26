# External Integrations — Readiness (§11)

Verifies that the architecture is **ready** to integrate the external systems an
industrial deployment needs, without implementing those integrations now. For
each system: the seam that exists, what a real integration would plug into, and
the readiness verdict. No business logic is changed to add an integration — each
is a new provider behind an existing interface.

> Principle: every external dependency is behind a **provider interface** with a
> mock/default implementation, selected by configuration. Swapping in a real
> vendor client is additive (new class + config), so Dispatch Engine, Rule
> Engine and AI Platform algorithms are untouched.

## Readiness matrix

| External system | Seam / interface | Default today | To integrate | Verdict |
|-----------------|------------------|---------------|--------------|---------|
| **IP telephony (SIP/PBX, call centre)** | `app.calls.providers.base` (`CallProvider`) + call queue + history | `MockCallProvider` | Add a SIP/PBX-backed `CallProvider` (events: ringing/answered/ended, ANI/DNIS); select via config | **Ready** |
| **External GIS / geocoding** | `app.gis.providers.base` (`GeoProvider`) with factory | Nominatim/Photon/Pelias/ArcGIS + `fake` | Point to self-hosted endpoints or add a provider subclass; caching seam already present | **Ready** |
| **Vehicle monitoring (AVL/GLONASS/GPS)** | `app.resources.tracking.position_provider` (`PositionProvider`) | Mock/manual positions | Add a telematics-backed `PositionProvider` streaming vehicle positions; feeds routing/ETA | **Ready** |
| **Corporate user directories (AD/LDAP)** | `app.admin.services.directory_service` + auth-method registry | Local users (PBKDF2) | Add a directory-backed identity source + authenticating gateway (see R1 in the security audit) | **Ready (auth layer pending)** |
| **Government / interagency systems** | `app.admin.services.integration_service` (integration registry) + REST API + typed schemas | Registry entries; no live calls | Add an outbound client per system behind the integration record; audit via existing `audit_logs` | **Ready** |
| **AI/ML services (ASR/NLP)** | `app.ai.interfaces.provider` + provider registry | `MockAIProvider` | Register a real ASR/NLP provider; pipeline and audit unchanged | **Ready** |
| **Observability backends (metrics/logs/alerts)** | `app.observability` exporter interface | In-memory + structured logs | Add a Prometheus/OTel/ELK exporter behind the interface | **Ready (vendor-neutral)** |
| **Shared cache / message bus** | `*_CACHE_BACKEND`, `GIS_REDIS_URL` config seam | In-memory | Provide a Redis backend implementing the cache interface | **Ready (config seam)** |

## Why these are "ready"

1. **Interface + factory + config** — each external concern is an abstract
   provider with at least one working implementation and a config-driven factory.
   A new integration is a new subclass, not a change to callers.
2. **Graceful degradation** — where an external dependency can be down (GIS,
   routing/OSRM), the system already falls back (cache, straight-line estimator),
   so integrating a real provider does not create a hard availability coupling.
3. **Auditable** — admin and export actions are recorded to `audit_logs`; an
   integration client can reuse the same recorder for outbound-call auditing.
4. **Vendor-neutral** — the Observability and secrets layers deliberately avoid
   binding to specific products, matching the "don't tie to a specific product"
   constraints from earlier stages.

## Cross-cutting prerequisites before enabling any live integration

- **Authentication** for inbound integrations and **credentials via the secrets
  manager** for outbound ones (never in the repo) — see
  [secrets.md](secrets.md) and the security audit R1.
- **Timeouts + retries + circuit-breaking** at each provider boundary (HTTP
  providers already take a configurable timeout; add retry/breaker per SLA).
- **Rate limiting / quotas** honouring the external system's limits.
- **Data-minimisation** — mask/limit PII crossing a boundary, consistent with
  the logging-masking policy.

## Verdict

The architecture is **integration-ready** for all systems the stage lists. No
integration is implemented here (per scope); each is an additive provider behind
an existing seam, plus configuration and the cross-cutting prerequisites above.
