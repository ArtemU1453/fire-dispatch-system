#!/usr/bin/env python3
"""Load / stress / soak / recovery test harness (Stage 16 §9).

A self-contained async HTTP load generator (stdlib + httpx, already a project
dependency — no new packages). It drives **read-only** endpoints of a running
instance, so it never mutates data and does not touch the Dispatch Engine's
decisions. It reports throughput, latency percentiles and error rate, and exits
non-zero when measurable criteria are violated, so it can gate a release.

Scenarios (``--scenario``):
  load      steady concurrency for a fixed duration (baseline SLO check)
  stress    ramp concurrency upward until latency/errors breach thresholds
  soak      low concurrency for a long duration (leak / degradation check)
  recovery  drive load, then keep probing so recovery-after-error is visible

Examples:
  python scripts/perf/loadtest.py --scenario load --base-url http://localhost:8000
  python scripts/perf/loadtest.py --scenario stress --max-concurrency 200
  python scripts/perf/loadtest.py --scenario soak --duration 1800

Measurable criteria are documented in docs/production/performance.md and can be
overridden with --p95-ms / --max-error-rate.
"""

from __future__ import annotations

import argparse
import asyncio
import statistics
import time
from dataclasses import dataclass, field

import httpx

# Read-only endpoints exercised by default. Health is always safe; the API
# read endpoints exercise the DB and serialization paths without mutating data.
DEFAULT_PATHS = [
    "/health",
    "/api/v1/health",
]


@dataclass
class Sample:
    latency_ms: float
    status: int
    ok: bool


@dataclass
class Result:
    samples: list[Sample] = field(default_factory=list)

    def add(self, s: Sample) -> None:
        self.samples.append(s)

    @property
    def count(self) -> int:
        return len(self.samples)

    @property
    def errors(self) -> int:
        return sum(1 for s in self.samples if not s.ok)

    @property
    def error_rate(self) -> float:
        return self.errors / self.count if self.count else 0.0

    def pct(self, p: float) -> float:
        if not self.samples:
            return 0.0
        lat = sorted(s.latency_ms for s in self.samples)
        k = max(0, min(len(lat) - 1, int(round((p / 100) * (len(lat) - 1)))))
        return lat[k]

    @property
    def mean_ms(self) -> float:
        if not self.samples:
            return 0.0
        return statistics.fmean(s.latency_ms for s in self.samples)


async def _worker(
    client: httpx.AsyncClient,
    paths: list[str],
    deadline: float,
    result: Result,
    stop: asyncio.Event,
) -> None:
    i = 0
    while time.monotonic() < deadline and not stop.is_set():
        path = paths[i % len(paths)]
        i += 1
        t0 = time.monotonic()
        try:
            resp = await client.get(path)
            ok = resp.status_code < 500
            result.add(Sample((time.monotonic() - t0) * 1000, resp.status_code, ok))
        except Exception:  # noqa: BLE001 - network/timeout counts as an error sample
            result.add(Sample((time.monotonic() - t0) * 1000, 0, False))


async def _run_phase(
    base_url: str, paths: list[str], concurrency: int, duration: float
) -> Result:
    result = Result()
    stop = asyncio.Event()
    limits = httpx.Limits(max_connections=concurrency + 10)
    timeout = httpx.Timeout(10.0)
    async with httpx.AsyncClient(
        base_url=base_url, limits=limits, timeout=timeout
    ) as client:
        deadline = time.monotonic() + duration
        workers = [
            asyncio.create_task(_worker(client, paths, deadline, result, stop))
            for _ in range(concurrency)
        ]
        await asyncio.gather(*workers)
    return result


def _report(name: str, r: Result, elapsed: float) -> None:
    rps = r.count / elapsed if elapsed else 0.0
    print(f"\n=== {name} ===")
    print(f"  requests      : {r.count}")
    print(f"  duration      : {elapsed:.1f}s")
    print(f"  throughput    : {rps:.1f} req/s")
    print(f"  errors        : {r.errors} ({r.error_rate * 100:.2f}%)")
    print(f"  latency mean  : {r.mean_ms:.1f} ms")
    print(f"  latency p50   : {r.pct(50):.1f} ms")
    print(f"  latency p95   : {r.pct(95):.1f} ms")
    print(f"  latency p99   : {r.pct(99):.1f} ms")


async def scenario_load(args) -> Result:
    t0 = time.monotonic()
    r = await _run_phase(args.base_url, args.paths, args.concurrency, args.duration)
    _report(f"load (c={args.concurrency}, {args.duration}s)", r, time.monotonic() - t0)
    return r


async def scenario_stress(args) -> Result:
    combined = Result()
    c = args.concurrency
    while c <= args.max_concurrency:
        t0 = time.monotonic()
        r = await _run_phase(args.base_url, args.paths, c, args.step_duration)
        _report(f"stress step c={c}", r, time.monotonic() - t0)
        combined.samples.extend(r.samples)
        if r.error_rate > args.max_error_rate or r.pct(95) > args.p95_ms:
            print(f"  -> breach at concurrency={c}; stopping ramp")
            break
        c *= 2
    return combined


async def scenario_soak(args) -> Result:
    t0 = time.monotonic()
    r = await _run_phase(
        args.base_url, args.paths, max(2, args.concurrency // 4), args.duration
    )
    _report(f"soak ({args.duration}s)", r, time.monotonic() - t0)
    return r


async def scenario_recovery(args) -> Result:
    print("recovery: applying load, then probing for recovery...")
    t0 = time.monotonic()
    load = await _run_phase(
        args.base_url, args.paths, args.max_concurrency, args.step_duration
    )
    _report("recovery: load phase", load, time.monotonic() - t0)
    # Probe phase: light traffic to observe error-rate returning to baseline.
    t1 = time.monotonic()
    probe = await _run_phase(args.base_url, args.paths, 2, args.step_duration)
    _report("recovery: probe phase", probe, time.monotonic() - t1)
    if probe.error_rate > args.max_error_rate:
        print("  -> did NOT recover to baseline error rate")
    else:
        print("  -> recovered to baseline error rate")
    combined = Result()
    combined.samples.extend(load.samples)
    combined.samples.extend(probe.samples)
    return combined


SCENARIOS = {
    "load": scenario_load,
    "stress": scenario_stress,
    "soak": scenario_soak,
    "recovery": scenario_recovery,
}


def _check_criteria(r: Result, args) -> int:
    """Return process exit code: 0 pass, 1 criteria violated."""
    print("\n=== criteria ===")
    ok = True
    er = r.error_rate * 100
    limit = args.max_error_rate * 100
    if r.error_rate > args.max_error_rate:
        print(f"  FAIL error rate {er:.2f}% > {limit:.2f}%")
        ok = False
    else:
        print(f"  PASS error rate {er:.2f}% <= {limit:.2f}%")
    p95 = r.pct(95)
    if p95 > args.p95_ms:
        print(f"  FAIL p95 {p95:.1f}ms > {args.p95_ms:.1f}ms")
        ok = False
    else:
        print(f"  PASS p95 {p95:.1f}ms <= {args.p95_ms:.1f}ms")
    return 0 if ok else 1


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="AI Dispatcher МЧС load-test harness")
    p.add_argument("--scenario", choices=SCENARIOS, default="load")
    p.add_argument("--base-url", default="http://localhost:8000")
    p.add_argument("--paths", nargs="+", default=DEFAULT_PATHS)
    p.add_argument("--concurrency", type=int, default=20)
    p.add_argument("--max-concurrency", type=int, default=160)
    p.add_argument("--duration", type=float, default=30.0)
    p.add_argument("--step-duration", type=float, default=10.0)
    # Measurable criteria (defaults mirror docs/production/performance.md).
    p.add_argument("--p95-ms", type=float, default=500.0)
    p.add_argument("--max-error-rate", type=float, default=0.01)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = asyncio.run(SCENARIOS[args.scenario](args))
    return _check_criteria(result, args)


if __name__ == "__main__":
    raise SystemExit(main())
