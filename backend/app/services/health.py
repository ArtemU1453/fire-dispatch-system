"""Health-check service.

Encapsulates the logic for reporting service health, including a lightweight
database connectivity probe. Lives in the service layer so the API endpoint
stays a thin adapter (Single Responsibility).
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.core.logging import get_logger
from app.schemas.health import HealthStatus
from app.services.base import BaseService

logger = get_logger(__name__)


class HealthService(BaseService):
    """Produce a :class:`HealthStatus` snapshot for the running service."""

    def __init__(
        self, session: AsyncSession, settings: Settings | None = None
    ) -> None:
        super().__init__(session)
        self._settings = settings or get_settings()

    async def check(self) -> HealthStatus:
        """Return the current health status, probing the database."""
        database_up = await self._ping_database()
        return HealthStatus(
            status="ok" if database_up else "degraded",
            app=self._settings.APP_NAME,
            version=self._settings.APP_VERSION,
            environment=self._settings.APP_ENV,
            database="up" if database_up else "down",
        )

    async def _ping_database(self) -> bool:
        """Execute a trivial query to verify database connectivity."""
        try:
            await self._session.execute(text("SELECT 1"))
            return True
        except Exception as exc:  # noqa: BLE001 - health probe must not raise
            logger.warning("Database health probe failed: %s", exc)
            return False
