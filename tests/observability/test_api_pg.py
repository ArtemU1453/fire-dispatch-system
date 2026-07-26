"""API tests for the observability endpoints (require PostgreSQL)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.observability.tracing import TRACE_ID_HEADER

pytestmark = pytest.mark.asyncio


async def test_health_endpoint(api_client: AsyncClient) -> None:
    resp = await api_client.get("/api/v1/observability/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["state"] in ("healthy", "degraded", "unhealthy")
    assert body["alive"] is True
    components = {c["component"] for c in body["components"]}
    assert {"database", "incidents", "calls", "ai_providers"} <= components
    # every request carries a Trace ID back
    assert TRACE_ID_HEADER in resp.headers


async def test_liveness_readiness(api_client: AsyncClient) -> None:
    live = await api_client.get("/api/v1/observability/health/live")
    assert live.status_code == 200
    assert live.json()["status"] == "alive"
    ready = await api_client.get("/api/v1/observability/health/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] in ("ready", "not_ready")


async def test_metrics_endpoint(api_client: AsyncClient) -> None:
    # generate some traffic first
    await api_client.get("/api/v1/observability/health")
    resp = await api_client.get("/api/v1/observability/metrics")
    assert resp.status_code == 200
    names = {m["name"] for m in resp.json()}
    assert "http_requests_total" in names
    assert "active_incidents" in names
    assert "service_uptime_seconds" in names


async def test_metrics_prometheus(api_client: AsyncClient) -> None:
    await api_client.get("/api/v1/observability/health")
    resp = await api_client.get("/api/v1/observability/metrics/prometheus")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    assert "http_requests_total" in resp.text


async def test_trace_id_propagation(api_client: AsyncClient) -> None:
    trace = "trace-abc-123"
    resp = await api_client.get(
        "/api/v1/observability/health", headers={TRACE_ID_HEADER: trace}
    )
    assert resp.headers[TRACE_ID_HEADER] == trace

    traces = await api_client.get("/api/v1/observability/traces")
    assert traces.status_code == 200
    assert any(t["trace_id"] == trace for t in traces.json())


async def test_traces_endpoint(api_client: AsyncClient) -> None:
    await api_client.get("/api/v1/observability/health")
    resp = await api_client.get("/api/v1/observability/traces")
    assert resp.status_code == 200
    spans = resp.json()
    assert spans
    assert all("trace_id" in s and "duration_ms" in s for s in spans)


async def test_logs_endpoint(api_client: AsyncClient) -> None:
    await api_client.get("/api/v1/observability/health")
    resp = await api_client.get("/api/v1/observability/logs", params={"limit": 50})
    assert resp.status_code == 200
    entries = resp.json()
    # the access-log line for the request should be captured
    assert entries
    assert all("timestamp" in e and "level" in e for e in entries)


async def test_alerts_endpoint(api_client: AsyncClient) -> None:
    resp = await api_client.get("/api/v1/observability/alerts")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_status_dashboard(api_client: AsyncClient) -> None:
    resp = await api_client.get("/api/v1/observability/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["state"] in ("healthy", "degraded", "unhealthy")
    assert "active_incidents" in body["key_metrics"]
    assert body["uptime_seconds"] >= 0
    assert isinstance(body["active_alerts"], int)
