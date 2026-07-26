"""Business-metric collectors (stage §3).

Collects operational gauges — active incidents, active calls, available units,
call-queue size, active users — by **reading** the existing tables (plain
counts). It does not duplicate any business logic; each probe is guarded so a
missing table simply yields 0.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# name → count query (all read-only, resilient to absent tables).
_QUERIES: dict[str, str] = {
    "active_incidents": (
        "SELECT count(*) FROM incidents WHERE is_deleted = false "
        "AND status NOT IN ('completed', 'archived', 'cancelled')"
    ),
    "active_calls": (
        "SELECT count(*) FROM calls WHERE is_deleted = false "
        "AND status NOT IN ('completed', 'cancelled')"
    ),
    "available_units": (
        "SELECT count(*) FROM units u "
        "JOIN availability_statuses a ON u.availability_status_id = a.id "
        "WHERE u.is_deleted = false AND a.is_available_for_dispatch = true"
    ),
    "call_queue_size": (
        "SELECT count(*) FROM call_queue WHERE is_deleted = false "
        "AND status IN ('waiting', 'assigned', 'in_progress')"
    ),
    "active_users": (
        "SELECT count(*) FROM user_sessions "
        "WHERE is_active = true AND revoked_at IS NULL"
    ),
}


class BusinessMetricsCollector:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def collect(self) -> dict[str, float]:
        gauges: dict[str, float] = {}
        for name, query in _QUERIES.items():
            gauges[name] = await self._count(query)
        return gauges

    async def _count(self, query: str) -> float:
        try:
            result = await self._session.execute(text(query))
            return float(result.scalar() or 0)
        except Exception:  # noqa: BLE001 - a metric probe must not raise
            return 0.0
