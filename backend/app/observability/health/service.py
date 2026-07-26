"""HealthService — aggregates every module's HealthProvider (stage §2)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.observability.health.provider import ComponentHealth, HealthState
from app.observability.health.registry import aggregate_state, build_providers


@dataclass(slots=True)
class HealthReport:
    state: HealthState
    ready: bool
    alive: bool
    version: str
    components: list[ComponentHealth]


class HealthService:
    def __init__(
        self, session: AsyncSession, settings: Settings | None = None
    ) -> None:
        self._settings = settings or get_settings()
        self._providers = build_providers(session, self._settings)

    async def components(self) -> list[ComponentHealth]:
        # Probes are independent — run them concurrently.
        return list(await asyncio.gather(*(p.health() for p in self._providers)))

    async def report(self) -> HealthReport:
        components = await self.components()
        return HealthReport(
            state=aggregate_state(components),
            ready=all(c.ready for c in components),
            alive=all(c.alive for c in components),
            version=self._settings.APP_VERSION,
            components=components,
        )

    async def readiness(self) -> bool:
        return all(c.ready for c in await self.components())

    async def liveness(self) -> bool:
        # Liveness is process-level: if we can answer, we are alive.
        return True
