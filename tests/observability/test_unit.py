"""Unit tests for observability primitives (no database)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from app.observability.alerts import (
    AlertRegistry,
    AlertService,
    AlertThresholds,
    AlertType,
)
from app.observability.health.provider import ComponentHealth, HealthState
from app.observability.logging.buffer import LogBuffer
from app.observability.metrics import MetricsRegistry
from app.observability.tracing import (
    get_trace_id,
    new_trace_id,
    reset_trace_id,
    set_trace_id,
)
from app.observability.utils.masking import mask_data, mask_value
from app.observability.utils.ring_buffer import RingBuffer


# ------------------------------------------------------------------ masking ---
def test_mask_sensitive_keys() -> None:
    assert mask_value("password", "secret") == "***"
    assert mask_value("api_key", "abc") == "***"
    assert mask_value("session_token", "t") == "***"
    assert mask_value("name", "Иван") == "Иван"


def test_mask_data_nested_and_truncate() -> None:
    data = {
        "user": {"password": "x", "email": "a@b.c"},
        "items": [{"secret": "s"}, {"ok": 1}],
        "text": "a" * 200,
    }
    masked = mask_data(data)
    assert masked["user"]["password"] == "***"
    assert masked["user"]["email"] == "a@b.c"
    assert masked["items"][0]["secret"] == "***"
    assert masked["text"].endswith("…") and len(masked["text"]) < 200


# -------------------------------------------------------------- ring buffer ---
def test_ring_buffer_recent_first_and_maxlen() -> None:
    rb: RingBuffer[int] = RingBuffer(maxlen=3)
    for i in range(5):
        rb.append(i)
    assert len(rb) == 3
    assert rb.snapshot() == [4, 3, 2]  # most recent first
    assert rb.snapshot(limit=1) == [4]


# ----------------------------------------------------------------- metrics ---
def test_metrics_registry() -> None:
    reg = MetricsRegistry()
    reg.inc("http_requests_total", method="GET", status="200")
    reg.inc("http_requests_total", method="GET", status="200")
    reg.inc("http_errors_total")
    reg.set_gauge("active_calls", 3, unit="count")
    for v in (10.0, 20.0, 30.0, 40.0):
        reg.observe("http_request_duration_ms", v)

    assert reg.counter_total("http_requests_total") == 2
    assert reg.counter_total("http_errors_total") == 1
    assert reg.gauge_value("active_calls") == 3
    assert reg.histogram_p95("http_request_duration_ms") >= 30.0

    names = {s.name for s in reg.snapshot()}
    assert "http_requests_total" in names
    assert "http_request_duration_ms_p95" in names
    assert "active_calls" in names


# ------------------------------------------------------------------- trace ---
def test_trace_context_set_get_reset() -> None:
    assert get_trace_id() is None
    tid = new_trace_id()
    token = set_trace_id(tid)
    assert get_trace_id() == tid
    reset_trace_id(token)
    assert get_trace_id() is None


# ------------------------------------------------------------- log buffer ---
def test_log_buffer_captures_and_masks() -> None:
    buffer = LogBuffer(maxlen=10)
    logger = logging.getLogger("test.obs")
    logger.addHandler(buffer)
    logger.setLevel(logging.INFO)
    token = set_trace_id("trace-123")
    try:
        logger.info("hello", extra={"password": "x", "user": "ivan"})
    finally:
        reset_trace_id(token)
    logger.removeHandler(buffer)

    entries = buffer.recent()
    assert entries
    entry = entries[0]
    assert entry.message == "hello"
    assert entry.trace_id == "trace-123"
    assert entry.fields["password"] == "***"
    assert entry.fields["user"] == "ivan"


# ------------------------------------------------------------------ alerts ---
def _component(name: str, state: HealthState) -> ComponentHealth:
    return ComponentHealth(
        component=name, state=state, ready=state is HealthState.HEALTHY,
        alive=True, version="1", checked_at=datetime.now(tz=UTC),
    )


def test_alert_service_generates_events() -> None:
    registry = AlertRegistry()
    service = AlertService(
        registry, AlertThresholds(error_rate=0.1, min_requests=10,
                                  response_time_p95_ms=100, queue_size=5)
    )
    metrics = MetricsRegistry()
    # 20 requests, 5 errors → 25% error rate (> 10%)
    for _ in range(20):
        metrics.inc("http_requests_total")
    for _ in range(5):
        metrics.inc("http_errors_total")
    metrics.observe("http_request_duration_ms", 500)  # > 100 ms p95
    metrics.set_gauge("call_queue_size", 12)           # > 5

    components = [
        _component("database", HealthState.HEALTHY),
        _component("telephony", HealthState.UNHEALTHY),
        _component("ai_providers", HealthState.DEGRADED),
    ]
    alerts = service.evaluate(components, metrics)
    types = {a.type for a in alerts}
    assert AlertType.SERVICE_UNAVAILABLE in types
    assert AlertType.HEALTH_CHECK_FAILED in types
    assert AlertType.ERROR_RATE_HIGH in types
    assert AlertType.RESPONSE_TIME_HIGH in types
    assert AlertType.QUEUE_OVERFLOW in types
    # events are recorded in the registry
    assert len(registry.recent()) == len(alerts)


def test_alert_service_quiet_when_healthy() -> None:
    registry = AlertRegistry()
    service = AlertService(registry)
    metrics = MetricsRegistry()
    components = [_component("database", HealthState.HEALTHY)]
    assert service.evaluate(components, metrics) == []
