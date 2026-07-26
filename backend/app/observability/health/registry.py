"""Assembles a HealthProvider per module and aggregates their health."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.observability.health.provider import (
    ComponentHealth,
    DatabaseHealthProvider,
    HealthProvider,
    HealthState,
    ModuleHealthProvider,
)

# Module → the main table whose reachability signals readiness.
_MODULE_TABLES: dict[str, str] = {
    "gis": "administrative_areas",
    "search": "resources",
    "rules": "rules",
    "dispatch": "dispatch_recommendations",
    "incidents": "incidents",
    "resources": "units",
    "calls": "calls",
    "admin": "app_settings",
    "ai": "ai_audit_log",
}


async def _telephony_ready() -> bool:
    from app.calls.deps import get_call_provider

    health = await get_call_provider().health_check()
    return health.healthy


async def _ai_ready() -> bool:
    from app.ai.deps import get_ai_registry

    provider = get_ai_registry().get()
    health = await provider.health_check()
    return health.healthy


def build_providers(
    session: AsyncSession, settings: Settings | None = None
) -> list[HealthProvider]:
    settings = settings or get_settings()
    version = settings.APP_VERSION
    providers: list[HealthProvider] = [
        DatabaseHealthProvider(session, version=version)
    ]
    for component, table in _MODULE_TABLES.items():
        providers.append(
            ModuleHealthProvider(
                component, version, session=session, table=table
            )
        )
    # Stateless module (no DB dependency of its own).
    providers.append(ModuleHealthProvider("routing", version))
    # Provider-backed modules (reuse their existing health_check).
    providers.append(
        ModuleHealthProvider("telephony", version, external=_telephony_ready)
    )
    providers.append(
        ModuleHealthProvider("ai_providers", version, external=_ai_ready)
    )
    return providers


def aggregate_state(components: Sequence[ComponentHealth]) -> HealthState:
    if not components:
        return HealthState.UNKNOWN
    states = {c.state for c in components}
    if HealthState.UNHEALTHY in states:
        return HealthState.UNHEALTHY
    if HealthState.DEGRADED in states:
        return HealthState.DEGRADED
    if states == {HealthState.HEALTHY}:
        return HealthState.HEALTHY
    return HealthState.DEGRADED
