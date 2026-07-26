"""Health checks (HealthProvider interface, per-module adapters, aggregation)."""

from __future__ import annotations

from app.observability.health.provider import (
    ComponentHealth,
    DatabaseHealthProvider,
    HealthProvider,
    HealthState,
    ModuleHealthProvider,
)
from app.observability.health.registry import aggregate_state, build_providers
from app.observability.health.service import HealthReport, HealthService

__all__ = [
    "ComponentHealth",
    "DatabaseHealthProvider",
    "HealthProvider",
    "HealthReport",
    "HealthService",
    "HealthState",
    "ModuleHealthProvider",
    "aggregate_state",
    "build_providers",
]
