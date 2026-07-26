# Security Audit (§10)

A pre-pilot security review of the AI Dispatcher МЧС backend across the areas the
stage requires: RBAC, input validation, logging, sensitive-data masking, error
handling, secrets management and API security. Each area lists what exists, the
findings, and a prioritised **risk register** with remediation.

> Scope note: this audit reviews the system **as built through Stage 15** plus
> the Stage 16 production-readiness additions. No business logic was changed to
> perform it. Severity uses **High / Medium / Low / Info**.

## Summary

The core building blocks for a secure deployment are present and sound: RBAC
resolution, Pydantic input validation, structured logging with sensitive-data
**masking**, a clean domain-error hierarchy, PBKDF2 password hashing, and (new
this stage) a secrets abstraction that keeps secrets out of the repository. The
**principal gap for production** is that request authentication is not yet
enforced at the API edge (by prior-stage constraint — no AD/LDAP/SSO/2FA), so
RBAC is available but not universally gating requests. This, along with CORS and
rate-limiting hardening, are the items to close before external exposure.

## Area-by-area

### 1. RBAC (authorization)
- **Present:** `RBACService` resolves effective permissions through roles,
  supports superuser bypass, custom roles/permissions in the database, and
  `require_permission`. Analytics and admin endpoints check permissions; export
  is gated by `analytics.export`.
- **Findings:** authorization is enforced where wired, but identity is treated
  as "open when no user is identified" in several modules, because no
  authentication layer exists yet (deliberate, per earlier constraints). RBAC is
  therefore only as strong as the (not-yet-present) authentication in front of
  it.

### 2. Input validation
- **Present:** Pydantic v2 request schemas across all modules; typed path/query
  params; domain `ValidationError` (422) distinct from schema errors. Database
  access is via the SQLAlchemy ORM with bound parameters.
- **Findings:** no user-controlled string is interpolated into SQL. One
  `text(f"SELECT 1 FROM {self._table} ...")` exists in the health provider, but
  `self._table` is an internal constant, not request input (Info).

### 3. Logging
- **Present:** centralised structured logging (`LOG_JSON` for aggregation),
  per-request Trace IDs, access logs with latency. Admin actions and analytics
  exports are written to an immutable `audit_logs` trail.
- **Findings:** logging is consistent and correlatable. Ensure `LOG_LEVEL=INFO`
  and `LOG_JSON=true` in production (the production env template does this).

### 4. Sensitive-data masking
- **Present:** `observability/utils/masking.py` masks sensitive keys
  (password, secret, token, api_key, authorization, credential, hashed_password,
  session_token, …) wholesale and truncates long/personal text (transcripts,
  prompts, bodies). Applied before logs/metrics are recorded.
- **Findings:** meets the "no passwords / secrets / keys / PII / full
  conversation texts in logs" requirement. Keep the sensitive-key list in step
  with new fields (Low, process item).

### 5. Error handling
- **Present:** `AppError` hierarchy → single handler mapping to HTTP codes
  (404/409/422/403). Domain errors return `{"detail": message}` only — no stack
  traces, no internal details.
- **Findings:** there is no explicit catch-all `Exception` handler, so an
  *unexpected* error falls through to FastAPI's default 500 ("Internal Server
  Error" — no traceback in the body **when `DEBUG=false`**). Risk is that
  `DEBUG=true` in production would expose details (see risks).

### 6. Secrets management
- **Present (new):** `app.config.secrets` abstraction — env / file / vault
  providers; `SECRETS_PROVIDER` selects the source; nothing sensitive is in the
  repository; the file-backup script excludes `.env`/`*.key`/`*.pem`.
- **Findings:** repository is clean of secrets; production template uses
  `SECRETS_PROVIDER=file`. Rotating secrets is an operator process (documented in
  secrets.md).

### 7. API security
- **Present:** typed endpoints, explicit status codes, CORS middleware driven by
  `CORS_ORIGINS`.
- **Findings:** default `CORS_ORIGINS=["*"]` **with** `allow_credentials=True`
  is unsafe for production and must be restricted to real origins; there is no
  request rate limiting; TLS is expected to be terminated at the ingress/LB.

## Risk register

| # | Risk | Sev | Area | Remediation |
|---|------|-----|------|-------------|
| R1 | **No authentication enforced at the API edge** — RBAC exists but requests are not universally authenticated | **High** | RBAC | Before external/pilot exposure, put an authenticating gateway/reverse-proxy (or an auth dependency) in front of the API and require an authenticated principal, then have endpoints call `require_permission`. Integrates with the corporate directory (see integrations-readiness) — no Dispatch/Rule/AI change needed. |
| R2 | **CORS `*` + credentials** would allow any origin in production | **High** | API | Set `CORS_ORIGINS` to the explicit dispatcher-workstation origins per environment (production template already narrows it); never combine `*` with credentials. |
| R3 | **`DEBUG=true` in production** would leak tracebacks/verbose errors | Medium | Errors | Enforce `DEBUG=false` in production (template does). Optionally add a catch-all `Exception` handler returning a generic 500 + Trace ID for support correlation. |
| R4 | **No request rate limiting** — brute-force / DoS exposure | Medium | API | Add rate limiting at the ingress or via the shared-cache (Redis) seam (§5); apply stricter limits to auth and export endpoints. |
| R5 | **TLS not enforced by the app** | Medium | API | Terminate TLS at the ingress/LB; redirect HTTP→HTTPS; enable HSTS. Deployment-level. |
| R6 | **Secrets rotation is manual** | Low | Secrets | Document and schedule rotation; when a vault is adopted, use short-lived leases (secrets.md). |
| R7 | **Masking key-list drift** — a newly named sensitive field might not be masked | Low | Logging | Keep `_SENSITIVE_KEYS` updated as part of code review; add a test when introducing new sensitive fields. |
| R8 | **Internal identifier in `text(f"… {self._table} …")`** | Info | Validation | Not user-controlled; if the table name ever becomes dynamic, switch to an allowlist / quoted identifier. |

## Recommended pre-pilot actions (checklist)

- [ ] R1 — front the API with authentication; require an authenticated principal.
- [ ] R2 — restrict `CORS_ORIGINS` per environment.
- [ ] R3 — confirm `DEBUG=false`; add a generic 500 handler with Trace ID.
- [ ] R4 — enable rate limiting at the edge.
- [ ] R5 — enforce TLS + HSTS at the ingress.
- [ ] Re-run this audit after the above and record results in the final report.
