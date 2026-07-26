"""Observability dependency providers (Dependency Injection wiring)."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.deps import SessionDep
from app.observability.alerts import AlertService
from app.observability.health import HealthService
from app.observability.services import DashboardService, MetricsService
from app.observability.state import alert_registry


def get_health_service(session: SessionDep) -> HealthService:
    return HealthService(session)


def get_metrics_service(session: SessionDep) -> MetricsService:
    return MetricsService(session)


def get_dashboard_service(session: SessionDep) -> DashboardService:
    return DashboardService(session)


def get_alert_service() -> AlertService:
    return AlertService(alert_registry)


HealthServiceDep = Annotated[HealthService, Depends(get_health_service)]
MetricsServiceDep = Annotated[MetricsService, Depends(get_metrics_service)]
DashboardServiceDep = Annotated[DashboardService, Depends(get_dashboard_service)]
AlertServiceDep = Annotated[AlertService, Depends(get_alert_service)]
