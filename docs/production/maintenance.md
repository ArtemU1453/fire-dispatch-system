# Maintenance & Operations (§12)

Routine processes to keep the AI Dispatcher МЧС system healthy in production.

## Cadence

| Task | Frequency | How |
|------|-----------|-----|
| Verify backups succeeded | Daily | check `backup_all.sh` logs / job status ([backup.md](backup.md)) |
| Restore drill | Quarterly | restore latest dump to a scratch DB ([recovery.md](recovery.md)) |
| Review error rate & latency | Daily | Observability dashboards; compare to load-test baseline ([performance.md](performance.md)) |
| Review audit logs | Weekly | `audit_logs` (admin actions, exports) |
| Apply security/dependency updates | Monthly / on CVE | bump pins, `make ci`, roll ([upgrade.md](upgrade.md)) |
| Rotate secrets | Per policy / on incident | [secrets.md](secrets.md) |
| Prune backups (retention) | Daily (automated) | `prune_backups.sh` |
| Database maintenance (vacuum/analyze) | Managed/auto | PostgreSQL autovacuum; monitor bloat |
| Re-run readiness checklist | Before each release | [../readiness-checklist.md](../readiness-checklist.md) |

## Monitoring & alerting

- **Health** — `/health` for liveness/readiness (aggregates per-module health
  providers).
- **Metrics** — request latency/error counters, business metrics, DB pool usage
  (Observability module). Export to Prometheus/OTel via the exporter seam.
- **Logs** — structured JSON (`LOG_JSON=true`), correlated by Trace ID; ship to
  the log aggregator. Sensitive data is masked.
- **Alerts** — wire the alert rules to the real notification channel at go-live
  (the module models alerts but sends none by default).

## Common operational tasks

- **Scale out/in** — change replica count behind the load balancer (§5). No data
  change; stateless.
- **Tune throughput** — adjust `DB_POOL_SIZE`/`DB_MAX_OVERFLOW`; enable the shared
  cache; add read replicas ([scaling.md](scaling.md), [performance.md](performance.md)).
- **Rotate a leaked secret** — update the secret source, roll the instances,
  review `audit_logs`.
- **Investigate an incident** — start from the Trace ID in the error log, follow
  it across access log, metrics and audit trail.

## Housekeeping

- Log/backup disk usage is bounded by rotation + `BACKUP_RETENTION_DAYS`.
- Observability ring buffers are in-memory and bounded (no unbounded growth).
- `make clean` clears local caches during development.

## Runbooks

The disaster-recovery procedures ([recovery.md](recovery.md)) are the runbooks
for database restore, configuration recovery, service restart and full-site loss.
Keep on-call contacts and escalation paths alongside them in your operations
system.
