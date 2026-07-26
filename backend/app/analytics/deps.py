"""Analytics dependency providers (Dependency Injection wiring)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import Depends, Query

from app.analytics.repositories import AnalyticsRepository
from app.analytics.utils.period import Period, PeriodKind
from app.analytics.utils.rbac import AnalyticsAccess
from app.api.deps import SessionDep
from app.core.exceptions import ValidationError


def get_period(
    period: PeriodKind = Query(default=PeriodKind.DAY),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
) -> Period:
    try:
        return Period.of(period, start=start, end=end)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def get_analytics_repo(session: SessionDep) -> AnalyticsRepository:
    return AnalyticsRepository(session)


def get_analytics_access(session: SessionDep) -> AnalyticsAccess:
    return AnalyticsAccess(session)


PeriodDep = Annotated[Period, Depends(get_period)]
AnalyticsRepoDep = Annotated[AnalyticsRepository, Depends(get_analytics_repo)]
AnalyticsAccessDep = Annotated[AnalyticsAccess, Depends(get_analytics_access)]
