"""Metrics exporter interface (backend-agnostic seam).

The platform stays independent of any monitoring product. An exporter translates
a metrics snapshot into some external format; concrete exporters (Prometheus text,
JSON, and later OpenTelemetry / OpenSearch) plug in here **without changing
instrumentation**. Only in-process formatters are provided at this stage — nothing
is shipped to an external system.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.observability.metrics.registry import MetricSample


class MetricsExporter(ABC):
    name: str = "base"

    @abstractmethod
    def export(self, samples: Sequence[MetricSample]) -> str:
        """Render a metrics snapshot into this exporter's format."""


class JsonExporter(MetricsExporter):
    name = "json"

    def export(self, samples: Sequence[MetricSample]) -> str:
        return json.dumps(
            [
                {
                    "name": s.name, "kind": s.kind.value, "value": s.value,
                    "labels": s.labels, "unit": s.unit,
                }
                for s in samples
            ],
            ensure_ascii=False,
        )


class PrometheusTextExporter(MetricsExporter):
    """A minimal Prometheus text-exposition formatter (illustrative only)."""

    name = "prometheus"

    def export(self, samples: Sequence[MetricSample]) -> str:
        lines: list[str] = []
        for s in samples:
            labels = ",".join(f'{k}="{v}"' for k, v in sorted(s.labels.items()))
            suffix = f"{{{labels}}}" if labels else ""
            lines.append(f"{s.name}{suffix} {s.value}")
        return "\n".join(lines) + ("\n" if lines else "")
