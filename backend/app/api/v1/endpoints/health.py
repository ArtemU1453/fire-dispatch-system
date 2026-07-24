"""Health-check endpoint.

A thin adapter that delegates all logic to :class:`HealthService`. Exposed both
at the API-versioned prefix and (via the app factory) at the top-level
``/health`` path for infrastructure probes.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import HealthServiceDep
from app.schemas.health import HealthStatus

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthStatus,
    summary="Service health check",
    description="Returns service metadata and database connectivity status.",
)
async def health(service: HealthServiceDep) -> HealthStatus:
    """Report whether the service and its dependencies are healthy."""
    return await service.check()
