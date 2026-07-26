# Performance & Load Testing (§9)

Scenarios and **measurable** criteria for validating that the system performs
acceptably under load before pilot operation. The harness is
`scripts/perf/loadtest.py` (async, stdlib + httpx, no new dependencies). It
drives **read-only** endpoints only, so it never mutates data or influences the
Dispatch Engine.

## Scenarios

| Scenario | Purpose | Command |
|----------|---------|---------|
| **Load** | Steady concurrency for a fixed time — verify baseline SLOs are met | `loadtest.py --scenario load` |
| **Stress** | Ramp concurrency until latency/error thresholds break — find the ceiling | `loadtest.py --scenario stress` |
| **Soak** | Low concurrency for a long time — detect leaks / gradual degradation | `loadtest.py --scenario soak --duration 3600` |
| **Recovery** | Overload, then probe — confirm the service returns to baseline after stress | `loadtest.py --scenario recovery` |

Run against a **staging** instance sized like production, with a
production-representative dataset (backup restore is a convenient seed).

```bash
python scripts/perf/loadtest.py --scenario load \
  --base-url https://dispatcher.staging.mchs.local \
  --concurrency 50 --duration 60
# or: make loadtest ARGS="--scenario stress --max-concurrency 200"
```

## Measurable criteria (targets)

The harness exits non-zero if the first two are violated, so it can gate a
release. Targets are the defaults (`--p95-ms`, `--max-error-rate`); tune to the
agreed SLO.

| Metric | Target (baseline load) | How measured |
|--------|------------------------|--------------|
| **Error rate** | ≤ 1% (5xx + transport errors) | harness `error_rate` |
| **Latency p95** | ≤ 500 ms for read endpoints | harness `p95` |
| **Latency p99** | ≤ 1000 ms | harness `p99` |
| **Throughput** | ≥ target req/s at the agreed concurrency without breaching latency | harness `throughput` |
| **Soak stability** | p95 drift < 20% over the soak; memory stable (no leak) | compare start/end + host metrics |
| **Recovery** | error rate returns to ≤ 1% within the probe phase after overload | harness recovery phase |

The endpoint-level latency is corroborated by the **Observability** module's
per-request latency metrics and the `/health` timing, so production behaviour
can be compared to the load-test baseline continuously.

## What to watch during a run

Correlate the harness output with the Observability dashboards/metrics:

- request latency histogram and error counters (per route),
- database pool saturation (`DB_POOL_SIZE`/`DB_MAX_OVERFLOW`) — the first thing
  to tune if latency climbs under load,
- CPU/memory of the API containers (host/orchestrator metrics),
- database CPU / slow queries.

## Tuning levers (no business-logic change)

- **DB pool** — raise `DB_POOL_SIZE` / `DB_MAX_OVERFLOW` for higher concurrency.
- **Horizontal scale** — add API replicas behind the load balancer (§5).
- **Shared cache** — enable the Redis cache backend to raise hit-rates across
  instances (§5).
- **Read replicas** — route read-only search/analytics to replicas (§5 seam).

All of these are configuration/deployment changes; none alters Dispatch Engine,
Rule Engine or AI Platform algorithms.
