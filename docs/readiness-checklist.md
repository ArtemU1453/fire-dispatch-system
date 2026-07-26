# Production Readiness Checklist (§13)

A go/no-go checklist for pilot operation of the AI Dispatcher МЧС system.
Machine-checkable items are automated by `scripts/verify/verify_readiness.sh`
(`make verify-readiness`); the rest require operator confirmation. Status legend:
**[x]** verified in this stage · **[ ]** operator/deployment action before go-live.

## REST APIs
- [x] All module routers mounted under `/api/v1` and listed in OpenAPI (`/docs`).
- [x] Consistent error contract (`{"detail": ...}`) with correct status codes.
- [x] Health endpoint (`/health`) for probes; per-module health providers.
- [ ] `CORS_ORIGINS` restricted to real workstation origins (security audit R2).

## Security
- [x] RBAC resolves permissions through roles; analytics/admin gated.
- [x] Passwords hashed (PBKDF2-HMAC-SHA256, constant-time verify).
- [x] Sensitive data masked in logs/metrics; no PII / secrets / full transcripts.
- [x] No secrets in the repository; secrets resolved via provider (§2).
- [x] Security audit performed with risk register + remediation (§10).
- [ ] Authentication layer in front of the API (security audit R1).
- [ ] `DEBUG=false`, TLS + HSTS at ingress, rate limiting (R3–R5).

## Performance
- [x] Load/stress/soak/recovery scenarios and harness provided (§9).
- [x] Measurable criteria defined (error rate ≤1%, p95 ≤500 ms, …).
- [ ] Criteria validated on a production-sized staging environment.

## Observability
- [x] Structured logging with Trace IDs; access + application logs.
- [x] Metrics registry (request + business metrics); dashboards.
- [x] Health aggregation; alert rules modelled (vendor-neutral).
- [ ] Exporters wired to the real metrics/log/alert backends.

## Logging
- [x] Centralised logging; `LOG_JSON` for aggregation.
- [x] Masking policy enforced.
- [ ] Log shipping/retention configured at the platform.

## Backup
- [x] Database + config + logs + uploads backup scripts (§3).
- [x] Retention policy + pruning; restore records schema revision.
- [ ] Scheduled job configured; off-site/durable target; WAL archiving (prod).

## Recovery
- [x] Documented DR procedures: DB restore, config, service restart, full site (§4).
- [x] RPO/RTO targets stated.
- [ ] Recovery drill executed and RTO recorded.

## Documentation
- [x] Architecture, module, API, DB-structure, configuration docs.
- [x] Developer, administrator, dispatcher guides.
- [x] Install, upgrade, backup, recovery, maintenance guides.
- [x] Production documentation index (`docs/production/`).

## Tests
- [x] Unit + integration (PostgreSQL) + API test suites; full suite green.
- [x] Migration verification (apply / no-drift / rollback / round-trip) (§8).
- [x] Secrets abstraction unit-tested.
- [ ] Full regression + load + recovery run on staging (final report §14).

## Build & deploy
- [x] Multi-stage Dockerfile, non-root, healthcheck; `.dockerignore`.
- [x] docker-compose with DB + API healthchecks; optional cache profile.
- [x] Makefile + reference CI (build/lint/test/migration/container), platform-agnostic.
- [x] Per-environment config templates (`deploy/env/`).
- [ ] Image published to the registry; migrations run as a deploy job.

## Configuration
- [x] Centralised, typed settings; nothing reads `os.environ` directly.
- [x] Environments: Development / Testing / Staging / Production.
- [x] No configuration hard-coded in source.

## Sign-off
- [ ] All unchecked items above resolved for the target environment.
- [ ] `make verify-readiness` green against staging.
- [ ] System owner (МЧС) approves pilot operation.
