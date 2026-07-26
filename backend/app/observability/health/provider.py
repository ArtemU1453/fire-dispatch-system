"""The ``HealthProvider`` interface and concrete providers (stage §2).

Every subsystem exposes its state through one interface:

    health()     — a full component-health snapshot
    readiness()  — is the component ready to serve? (dependencies reachable)
    liveness()   — is the component alive? (process/module running)
    version()    — the component version

Existing modules are **not modified**: the observability platform supplies a
``HealthProvider`` adapter per module (DB-table-backed or provider-backed), which
gives every module a health provider without touching its code.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class HealthState(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class ComponentHealth:
    component: str
    state: HealthState
    ready: bool
    alive: bool
    version: str
    detail: str | None = None
    latency_ms: float | None = None
    checked_at: datetime | None = None


class HealthProvider(ABC):
    """Interface every subsystem's health adapter implements."""

    component: str = "component"
    _version: str = "0"

    @abstractmethod
    async def readiness(self) -> bool:
        """Whether the component's dependencies are reachable."""

    async def liveness(self) -> bool:
        """Whether the component/process is alive (default: yes)."""
        return True

    def version(self) -> str:
        return self._version

    async def health(self) -> ComponentHealth:
        start = time.perf_counter()
        alive = await self.liveness()
        ready = False
        detail: str | None = None
        try:
            ready = await self.readiness()
        except Exception as exc:  # noqa: BLE001 - a probe must not raise
            detail = str(exc)
        state = (
            HealthState.HEALTHY
            if alive and ready
            else HealthState.UNHEALTHY
            if not alive
            else HealthState.DEGRADED
        )
        return ComponentHealth(
            component=self.component,
            state=state,
            ready=ready,
            alive=alive,
            version=self.version(),
            detail=detail,
            latency_ms=round((time.perf_counter() - start) * 1000, 2),
            checked_at=datetime.now(tz=UTC),
        )


class DatabaseHealthProvider(HealthProvider):
    """Probes database connectivity with ``SELECT 1``."""

    component = "database"

    def __init__(self, session: AsyncSession, *, version: str = "n/a") -> None:
        self._session = session
        self._version = version

    async def readiness(self) -> bool:
        await self._session.execute(text("SELECT 1"))
        return True


class ModuleHealthProvider(HealthProvider):
    """A health adapter for an existing module.

    Readiness is derived from either a lightweight table probe (the module's main
    table is reachable) or an external async check (e.g. a provider's
    ``health_check``). Modules with neither are ready as long as they are alive.
    """

    def __init__(
        self,
        component: str,
        version: str,
        *,
        session: AsyncSession | None = None,
        table: str | None = None,
        external: Callable[[], Awaitable[bool]] | None = None,
    ) -> None:
        self.component = component
        self._version = version
        self._session = session
        self._table = table
        self._external = external

    async def readiness(self) -> bool:
        if self._external is not None:
            return await self._external()
        if self._table is not None and self._session is not None:
            # Identifier is a fixed, code-provided table name (never user input).
            await self._session.execute(
                text(f"SELECT 1 FROM {self._table} LIMIT 1")
            )
            return True
        return True
