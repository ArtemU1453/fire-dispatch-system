"""AlertService — rule-based alert **event generation** (stage §6).

Evaluates rules against the current health and metrics and **generates alert
events** into an in-memory registry. It does **not send** any notification — real
delivery (email / SMS / external systems / SIEM) is a later concern; this stage
only produces the events other systems could consume.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

from app.observability.health.provider import ComponentHealth, HealthState
from app.observability.metrics.registry import MetricsRegistry
from app.observability.utils.ring_buffer import RingBuffer


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(str, Enum):
    SERVICE_UNAVAILABLE = "service_unavailable"
    ERROR_RATE_HIGH = "error_rate_high"
    RESPONSE_TIME_HIGH = "response_time_high"
    HEALTH_CHECK_FAILED = "health_check_failed"
    QUEUE_OVERFLOW = "queue_overflow"


@dataclass(slots=True)
class Alert:
    id: str
    type: AlertType
    severity: AlertSeverity
    component: str
    message: str
    triggered_at: datetime
    value: float | None = None
    threshold: float | None = None


@dataclass(slots=True)
class AlertThresholds:
    error_rate: float = 0.10          # fraction of requests that are 5xx
    min_requests: int = 20            # don't alert on error rate below this volume
    response_time_p95_ms: float = 1000.0
    queue_size: float = 50.0


@dataclass
class AlertRegistry:
    """In-memory store of generated alert events."""

    _events: RingBuffer[Alert] = field(default_factory=lambda: RingBuffer(500))

    def add(self, alert: Alert) -> None:
        self._events.append(alert)

    def recent(self, *, limit: int = 100) -> list[Alert]:
        return self._events.snapshot(limit=limit)

    def clear(self) -> None:
        self._events.clear()


def _alert(
    type_: AlertType, severity: AlertSeverity, component: str, message: str,
    *, value: float | None = None, threshold: float | None = None,
) -> Alert:
    return Alert(
        id=uuid.uuid4().hex,
        type=type_,
        severity=severity,
        component=component,
        message=message,
        triggered_at=datetime.now(tz=UTC),
        value=value,
        threshold=threshold,
    )


class AlertService:
    def __init__(
        self,
        registry: AlertRegistry,
        thresholds: AlertThresholds | None = None,
    ) -> None:
        self._registry = registry
        self._t = thresholds or AlertThresholds()

    def evaluate(
        self,
        components: Sequence[ComponentHealth],
        metrics: MetricsRegistry,
    ) -> list[Alert]:
        """Evaluate all rules; record and return any triggered alerts."""
        alerts: list[Alert] = []

        # Rule: service unavailable / health-check failure.
        for c in components:
            if c.state is HealthState.UNHEALTHY:
                alerts.append(_alert(
                    AlertType.SERVICE_UNAVAILABLE, AlertSeverity.CRITICAL,
                    c.component, f"Компонент недоступен: {c.component}",
                ))
            elif c.state is HealthState.DEGRADED:
                alerts.append(_alert(
                    AlertType.HEALTH_CHECK_FAILED, AlertSeverity.WARNING,
                    c.component, f"Health-check не пройден: {c.component}",
                ))

        # Rule: error rate too high.
        total = metrics.counter_total("http_requests_total")
        errors = metrics.counter_total("http_errors_total")
        if total >= self._t.min_requests:
            rate = errors / total if total else 0.0
            if rate > self._t.error_rate:
                alerts.append(_alert(
                    AlertType.ERROR_RATE_HIGH, AlertSeverity.CRITICAL, "api",
                    f"Высокий процент ошибок: {rate:.0%}",
                    value=round(rate, 3), threshold=self._t.error_rate,
                ))

        # Rule: response time too high (p95).
        p95 = metrics.histogram_p95("http_request_duration_ms")
        if p95 > self._t.response_time_p95_ms:
            alerts.append(_alert(
                AlertType.RESPONSE_TIME_HIGH, AlertSeverity.WARNING, "api",
                f"Превышено время ответа (p95={p95:.0f} мс)",
                value=round(p95, 1), threshold=self._t.response_time_p95_ms,
            ))

        # Rule: queue overflow.
        queue = metrics.gauge_value("call_queue_size")
        if queue > self._t.queue_size:
            alerts.append(_alert(
                AlertType.QUEUE_OVERFLOW, AlertSeverity.WARNING, "calls",
                f"Переполнение очереди вызовов ({int(queue)})",
                value=queue, threshold=self._t.queue_size,
            ))

        for alert in alerts:
            self._registry.add(alert)
        return alerts
