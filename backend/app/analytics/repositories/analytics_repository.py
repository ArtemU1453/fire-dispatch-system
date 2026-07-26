"""Read-only aggregate queries over existing modules' data (stage §2).

Every method is a **read** over the existing ORM models (incidents, calls,
dispatch recommendations, dispatches, resource assignments, units, catalogs) —
the analytics platform never writes to or changes any of them. Aggregation is
pushed into the database (counts / averages / groupings) for performance.
"""

from __future__ import annotations

from sqlalchemy import String, cast, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.utils.period import Period
from app.calls.models.entities import Call
from app.dispatch.models import Recommendation
from app.incidents.models.entities import (
    Incident,
    IncidentDispatch,
    IncidentRecommendation,
)
from app.models import AdministrativeArea, IncidentType
from app.resources.models.entities import ResourceAssignment, Unit


def _epoch(later, earlier):
    return func.extract("epoch", later - earlier)


class AnalyticsRepository:
    """Aggregate reads for KPIs, statistics and trends."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _scalar(self, stmt) -> float | None:
        value = (await self._session.execute(stmt)).scalar()
        return float(value) if value is not None else None

    # ----------------------------------------------------------- counts ---
    async def call_count(self, p: Period) -> float:
        stmt = select(func.count(Call.id)).where(
            Call.is_deleted.is_(False),
            Call.received_at >= p.start, Call.received_at < p.end,
        )
        return await self._scalar(stmt) or 0.0

    async def incident_count(self, p: Period) -> float:
        stmt = select(func.count(Incident.id)).where(
            Incident.is_deleted.is_(False),
            Incident.reported_at >= p.start, Incident.reported_at < p.end,
        )
        return await self._scalar(stmt) or 0.0

    # -------------------------------------------------------- durations ---
    async def avg_call_registration_seconds(self, p: Period) -> float | None:
        stmt = select(func.avg(Call.wait_seconds)).where(
            Call.is_deleted.is_(False),
            Call.answered_at.is_not(None),
            Call.received_at >= p.start, Call.received_at < p.end,
        )
        return await self._scalar(stmt)

    async def avg_decision_seconds(self, p: Period) -> float | None:
        stmt = select(
            func.avg(_epoch(Incident.confirmed_at, Incident.reported_at))
        ).where(
            Incident.is_deleted.is_(False),
            Incident.confirmed_at.is_not(None),
            Incident.reported_at >= p.start, Incident.reported_at < p.end,
        )
        return await self._scalar(stmt)

    async def avg_assignment_seconds(self, p: Period) -> float | None:
        first = (
            select(
                IncidentDispatch.incident_id.label("iid"),
                func.min(IncidentDispatch.assigned_at).label("first_at"),
            )
            .group_by(IncidentDispatch.incident_id)
            .subquery()
        )
        stmt = (
            select(func.avg(_epoch(first.c.first_at, Incident.reported_at)))
            .select_from(Incident)
            .join(first, first.c.iid == Incident.id)
            .where(
                Incident.is_deleted.is_(False),
                Incident.reported_at >= p.start, Incident.reported_at < p.end,
            )
        )
        return await self._scalar(stmt)

    async def avg_processing_seconds(self, p: Period) -> float | None:
        stmt = select(
            func.avg(_epoch(Incident.closed_at, Incident.reported_at))
        ).where(
            Incident.is_deleted.is_(False),
            Incident.closed_at.is_not(None),
            Incident.reported_at >= p.start, Incident.reported_at < p.end,
        )
        return await self._scalar(stmt)

    # ------------------------------------------------------------ loads ---
    async def dispatcher_load(self, p: Period) -> float | None:
        """Average number of calls handled per (active) dispatcher."""
        total = select(func.count(Call.id)).where(
            Call.is_deleted.is_(False),
            Call.dispatcher_user_id.is_not(None),
            Call.received_at >= p.start, Call.received_at < p.end,
        )
        distinct_disp = select(
            func.count(distinct(Call.dispatcher_user_id))
        ).where(
            Call.is_deleted.is_(False),
            Call.dispatcher_user_id.is_not(None),
            Call.received_at >= p.start, Call.received_at < p.end,
        )
        n = await self._scalar(distinct_disp) or 0.0
        t = await self._scalar(total) or 0.0
        return round(t / n, 2) if n else None

    async def unit_load(self, p: Period) -> float | None:
        """Average number of incident assignments per (used) unit."""
        total = select(func.count(ResourceAssignment.id)).where(
            ResourceAssignment.is_deleted.is_(False),
            ResourceAssignment.assigned_at >= p.start,
            ResourceAssignment.assigned_at < p.end,
        )
        distinct_units = select(
            func.count(distinct(ResourceAssignment.unit_id))
        ).where(
            ResourceAssignment.is_deleted.is_(False),
            ResourceAssignment.assigned_at >= p.start,
            ResourceAssignment.assigned_at < p.end,
        )
        n = await self._scalar(distinct_units) or 0.0
        t = await self._scalar(total) or 0.0
        return round(t / n, 2) if n else None

    async def resource_utilization_pct(self, p: Period) -> float | None:
        """Share of units currently not available for dispatch (snapshot)."""
        from app.models import AvailabilityStatus

        total = select(func.count(Unit.id)).where(Unit.is_deleted.is_(False))
        busy = (
            select(func.count(Unit.id))
            .select_from(Unit)
            .join(
                AvailabilityStatus,
                AvailabilityStatus.id == Unit.availability_status_id,
            )
            .where(
                Unit.is_deleted.is_(False),
                AvailabilityStatus.is_available_for_dispatch.is_(False),
            )
        )
        t = await self._scalar(total) or 0.0
        b = await self._scalar(busy) or 0.0
        return round(100.0 * b / t, 1) if t else None

    # -------------------------------------------------- recommendations ---
    async def confirmed_recommendations_pct(self, p: Period) -> float | None:
        """Share of recommended incidents that led to dispatched units."""
        with_rec = (
            select(distinct(Recommendation.incident_id))
            .join(Incident, Incident.id == Recommendation.incident_id)
            .where(
                Incident.is_deleted.is_(False),
                Incident.reported_at >= p.start, Incident.reported_at < p.end,
            )
            .subquery()
        )
        denom = select(func.count()).select_from(with_rec)
        numer = (
            select(func.count(distinct(IncidentDispatch.incident_id)))
            .where(IncidentDispatch.incident_id.in_(select(with_rec)))
        )
        d = await self._scalar(denom) or 0.0
        n = await self._scalar(numer) or 0.0
        return round(100.0 * n / d, 1) if d else None

    async def recommendation_change_frequency(self, p: Period) -> float | None:
        """Average number of recommendation revisions per incident."""
        recs = (
            select(func.count(IncidentRecommendation.id))
            .join(Incident, Incident.id == IncidentRecommendation.incident_id)
            .where(
                Incident.is_deleted.is_(False),
                Incident.reported_at >= p.start, Incident.reported_at < p.end,
            )
        )
        incidents_with = (
            select(func.count(distinct(IncidentRecommendation.incident_id)))
            .join(Incident, Incident.id == IncidentRecommendation.incident_id)
            .where(
                Incident.is_deleted.is_(False),
                Incident.reported_at >= p.start, Incident.reported_at < p.end,
            )
        )
        total = await self._scalar(recs) or 0.0
        n = await self._scalar(incidents_with) or 0.0
        return round(total / n, 2) if n else None

    async def avg_units_per_incident(self, p: Period) -> float | None:
        dispatches = (
            select(func.count(IncidentDispatch.id))
            .join(Incident, Incident.id == IncidentDispatch.incident_id)
            .where(
                Incident.is_deleted.is_(False),
                Incident.reported_at >= p.start, Incident.reported_at < p.end,
            )
        )
        incidents_with = (
            select(func.count(distinct(IncidentDispatch.incident_id)))
            .join(Incident, Incident.id == IncidentDispatch.incident_id)
            .where(
                Incident.is_deleted.is_(False),
                Incident.reported_at >= p.start, Incident.reported_at < p.end,
            )
        )
        total = await self._scalar(dispatches) or 0.0
        n = await self._scalar(incidents_with) or 0.0
        return round(total / n, 2) if n else None

    # --------------------------------------------------- distributions ---
    async def incident_type_distribution(self, p: Period) -> list[tuple[str, int]]:
        stmt = (
            select(
                func.coalesce(
                    IncidentType.name, cast(Incident.category, String)
                ).label("label"),
                func.count(Incident.id),
            )
            .select_from(Incident)
            .outerjoin(IncidentType, IncidentType.id == Incident.incident_type_id)
            .where(
                Incident.is_deleted.is_(False),
                Incident.reported_at >= p.start, Incident.reported_at < p.end,
            )
            .group_by("label")
            .order_by(func.count(Incident.id).desc())
        )
        rows = (await self._session.execute(stmt)).all()
        return [(str(label), int(count)) for label, count in rows]

    async def district_distribution(self, p: Period) -> list[tuple[str, int]]:
        stmt = (
            select(
                func.coalesce(AdministrativeArea.name, "—").label("label"),
                func.count(Incident.id),
            )
            .select_from(Incident)
            .outerjoin(
                AdministrativeArea,
                AdministrativeArea.id == Incident.administrative_area_id,
            )
            .where(
                Incident.is_deleted.is_(False),
                Incident.reported_at >= p.start, Incident.reported_at < p.end,
            )
            .group_by("label")
            .order_by(func.count(Incident.id).desc())
        )
        rows = (await self._session.execute(stmt)).all()
        return [(str(label), int(count)) for label, count in rows]

    async def unit_load_distribution(
        self, p: Period, *, limit: int = 20
    ) -> list[tuple[str, int]]:
        stmt = (
            select(Unit.code, func.count(ResourceAssignment.id))
            .select_from(ResourceAssignment)
            .join(Unit, Unit.id == ResourceAssignment.unit_id)
            .where(
                ResourceAssignment.is_deleted.is_(False),
                ResourceAssignment.assigned_at >= p.start,
                ResourceAssignment.assigned_at < p.end,
            )
            .group_by(Unit.code)
            .order_by(func.count(ResourceAssignment.id).desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).all()
        return [(str(code), int(count)) for code, count in rows]

    async def call_dynamics(self, p: Period) -> list[tuple[str, int]]:
        bucket = func.date_trunc("day", Call.received_at)
        stmt = (
            select(bucket.label("day"), func.count(Call.id))
            .where(
                Call.is_deleted.is_(False),
                Call.received_at >= p.start, Call.received_at < p.end,
            )
            .group_by("day")
            .order_by("day")
        )
        rows = (await self._session.execute(stmt)).all()
        return [(day.isoformat(), int(count)) for day, count in rows]
