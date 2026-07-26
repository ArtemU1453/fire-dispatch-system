"""In-memory, backend-agnostic metrics registry (stage §3).

Counters, gauges and histograms are kept in memory with a simple, dependency-free
API. It is **not tied to any monitoring system** — an exporter can later translate
a snapshot into Prometheus / OpenTelemetry format without changing instrumentation
call sites.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from enum import Enum

Labels = tuple[tuple[str, str], ...]


class MetricKind(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


@dataclass(slots=True)
class MetricSample:
    name: str
    kind: MetricKind
    value: float
    labels: dict[str, str] = field(default_factory=dict)
    unit: str | None = None


def _key(name: str, labels: dict[str, str]) -> tuple[str, Labels]:
    return name, tuple(sorted(labels.items()))


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(round((pct / 100) * (len(ordered) - 1))))
    return ordered[idx]


class MetricsRegistry:
    """Thread-safe registry of counters, gauges and histograms."""

    def __init__(self) -> None:
        self._counters: dict[tuple[str, Labels], float] = {}
        self._gauges: dict[tuple[str, Labels], float] = {}
        self._histograms: dict[tuple[str, Labels], list[float]] = {}
        self._units: dict[str, str] = {}
        self._lock = threading.Lock()

    def inc(self, name: str, value: float = 1.0, **labels: str) -> None:
        with self._lock:
            self._counters[_key(name, labels)] = (
                self._counters.get(_key(name, labels), 0.0) + value
            )

    def set_gauge(
        self, name: str, value: float, *, unit: str | None = None, **labels: str
    ) -> None:
        with self._lock:
            self._gauges[_key(name, labels)] = value
            if unit:
                self._units[name] = unit

    def observe(
        self, name: str, value: float, *, unit: str | None = "ms", **labels: str
    ) -> None:
        with self._lock:
            self._histograms.setdefault(_key(name, labels), []).append(value)
            if unit:
                self._units[name] = unit

    def snapshot(self) -> list[MetricSample]:
        """Flatten all metrics into samples (histograms → derived stats)."""
        with self._lock:
            samples: list[MetricSample] = []
            for (name, labels), value in self._counters.items():
                samples.append(
                    MetricSample(name, MetricKind.COUNTER, value, dict(labels))
                )
            for (name, labels), value in self._gauges.items():
                samples.append(
                    MetricSample(
                        name, MetricKind.GAUGE, value, dict(labels),
                        unit=self._units.get(name),
                    )
                )
            for (name, labels), values in self._histograms.items():
                lbl = dict(labels)
                unit = self._units.get(name, "ms")
                count = len(values)
                avg = sum(values) / count if count else 0.0
                samples.append(
                    MetricSample(f"{name}_count", MetricKind.HISTOGRAM, count, lbl)
                )
                samples.append(
                    MetricSample(
                        f"{name}_avg", MetricKind.HISTOGRAM,
                        round(avg, 2), lbl, unit=unit,
                    )
                )
                samples.append(
                    MetricSample(
                        f"{name}_p95", MetricKind.HISTOGRAM,
                        round(_percentile(values, 95), 2), lbl, unit=unit,
                    )
                )
                samples.append(
                    MetricSample(
                        f"{name}_max", MetricKind.HISTOGRAM,
                        round(max(values), 2), lbl, unit=unit,
                    )
                )
            return samples

    # --- convenience readers used by alert rules -------------------------
    def counter_total(self, name: str) -> float:
        with self._lock:
            return sum(
                v for (n, _), v in self._counters.items() if n == name
            )

    def gauge_value(self, name: str, default: float = 0.0) -> float:
        with self._lock:
            for (n, _), v in self._gauges.items():
                if n == name:
                    return v
        return default

    def histogram_p95(self, name: str) -> float:
        with self._lock:
            values: list[float] = []
            for (n, _), vals in self._histograms.items():
                if n == name:
                    values.extend(vals)
        return _percentile(values, 95)

    def clear(self) -> None:
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
