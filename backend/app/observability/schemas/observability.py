"""Pydantic schemas for the observability platform (stage §8)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.observability.alerts import AlertSeverity, AlertType
from app.observability.health import HealthState
from app.observability.metrics import MetricKind
from app.schemas.common import SchemaBase


class ComponentHealthResponse(SchemaBase):
    component: str
    state: HealthState
    ready: bool
    alive: bool
    version: str
    detail: str | None = None
    latency_ms: float | None = None
    checked_at: datetime | None = None


class HealthResponse(SchemaBase):
    state: HealthState
    ready: bool
    alive: bool
    version: str
    components: list[ComponentHealthResponse] = []


class ProbeResponse(SchemaBase):
    status: str
    version: str | None = None


class MetricResponse(SchemaBase):
    name: str
    kind: MetricKind
    value: float
    labels: dict[str, str] = {}
    unit: str | None = None


class TraceResponse(SchemaBase):
    trace_id: str
    method: str
    path: str
    status_code: int
    duration_ms: float
    started_at: datetime
    error: str | None = None


class AlertResponse(SchemaBase):
    id: str
    type: AlertType
    severity: AlertSeverity
    component: str
    message: str
    value: float | None = None
    threshold: float | None = None
    triggered_at: datetime


class LogEntryResponse(SchemaBase):
    timestamp: datetime
    level: str
    logger: str
    message: str
    trace_id: str | None = None
    fields: dict[str, Any] = {}


class DashboardComponent(SchemaBase):
    component: str
    state: HealthState


class DashboardResponse(SchemaBase):
    state: HealthState
    version: str
    uptime_seconds: float
    components: list[DashboardComponent] = []
    key_metrics: dict[str, float] = {}
    active_alerts: int
