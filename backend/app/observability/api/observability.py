"""Observability REST endpoints (Dashboard API, stage §7).

    GET /observability/health   · /health/live · /health/ready
    GET /observability/metrics  · /metrics/prometheus
    GET /observability/logs     · /traces · /alerts · /status
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse

from app.observability.deps import (
    AlertServiceDep,
    DashboardServiceDep,
    HealthServiceDep,
    MetricsServiceDep,
)
from app.observability.exporters import PrometheusTextExporter
from app.observability.schemas import (
    AlertResponse,
    ComponentHealthResponse,
    DashboardComponent,
    DashboardResponse,
    HealthResponse,
    LogEntryResponse,
    MetricResponse,
    ProbeResponse,
    TraceResponse,
)
from app.observability.state import alert_registry, log_buffer, trace_recorder

router = APIRouter(prefix="/observability", tags=["observability"])


# ------------------------------------------------------------------ health ---
@router.get("/health", response_model=HealthResponse, summary="Aggregated health")
async def health(service: HealthServiceDep) -> HealthResponse:
    report = await service.report()
    return HealthResponse(
        state=report.state, ready=report.ready, alive=report.alive,
        version=report.version,
        components=[
            ComponentHealthResponse.model_validate(c) for c in report.components
        ],
    )


@router.get("/health/live", response_model=ProbeResponse, summary="Liveness probe")
async def liveness(service: HealthServiceDep) -> ProbeResponse:
    alive = await service.liveness()
    return ProbeResponse(status="alive" if alive else "dead")


@router.get("/health/ready", response_model=ProbeResponse, summary="Readiness probe")
async def readiness(service: HealthServiceDep) -> ProbeResponse:
    ready = await service.readiness()
    return ProbeResponse(status="ready" if ready else "not_ready")


# ----------------------------------------------------------------- metrics ---
@router.get("/metrics", response_model=list[MetricResponse], summary="Metrics")
async def metrics(service: MetricsServiceDep) -> list[MetricResponse]:
    samples = await service.snapshot()
    return [MetricResponse.model_validate(s) for s in samples]


@router.get(
    "/metrics/prometheus", response_class=PlainTextResponse,
    summary="Metrics in Prometheus text format",
)
async def metrics_prometheus(service: MetricsServiceDep) -> PlainTextResponse:
    samples = await service.snapshot()
    return PlainTextResponse(PrometheusTextExporter().export(samples))


# -------------------------------------------------------------------- logs ---
@router.get("/logs", response_model=list[LogEntryResponse], summary="Recent logs")
async def logs(
    level: str | None = Query(default=None),
    trace_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[LogEntryResponse]:
    entries = log_buffer.recent(limit=limit, level=level, trace_id=trace_id)
    return [LogEntryResponse.model_validate(e) for e in entries]


# ------------------------------------------------------------------ traces ---
@router.get("/traces", response_model=list[TraceResponse], summary="Recent traces")
async def traces(
    limit: int = Query(default=100, ge=1, le=500),
) -> list[TraceResponse]:
    return [
        TraceResponse.model_validate(s) for s in trace_recorder.recent(limit=limit)
    ]


# ------------------------------------------------------------------ alerts ---
@router.get("/alerts", response_model=list[AlertResponse], summary="Alerts")
async def alerts(
    alert_service: AlertServiceDep,
    health_service: HealthServiceDep,
    metrics_service: MetricsServiceDep,
    evaluate: bool = Query(default=True, description="Re-evaluate rules now"),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[AlertResponse]:
    if evaluate:
        components = await health_service.components()
        await metrics_service.refresh_business()
        alert_service.evaluate(components, metrics_service.registry)
    return [AlertResponse.model_validate(a) for a in alert_registry.recent(limit=limit)]


# ------------------------------------------------------------------ status ---
@router.get("/status", response_model=DashboardResponse, summary="System status")
async def status(service: DashboardServiceDep) -> DashboardResponse:
    summary = await service.status()
    return DashboardResponse(
        state=summary.state, version=summary.version,
        uptime_seconds=summary.uptime_seconds,
        components=[
            DashboardComponent(component=c.component, state=c.state)
            for c in summary.components
        ],
        key_metrics=summary.key_metrics, active_alerts=summary.active_alerts,
    )
