"""Reporting periods / time windows (stage §5).

A period bounds every KPI, statistic and report: daily, weekly, monthly or a
custom range. Windows are rolling (end-inclusive to ``end``, defaulting to now),
which keeps them deterministic and easy to test.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum


class PeriodKind(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    CUSTOM = "custom"


_SPANS = {
    PeriodKind.DAY: timedelta(days=1),
    PeriodKind.WEEK: timedelta(days=7),
    PeriodKind.MONTH: timedelta(days=30),
}


@dataclass(slots=True)
class Period:
    kind: PeriodKind
    start: datetime
    end: datetime

    @classmethod
    def of(
        cls,
        kind: PeriodKind = PeriodKind.DAY,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> Period:
        now = datetime.now(tz=UTC)
        end = end or now
        if kind is PeriodKind.CUSTOM:
            if start is None:
                raise ValueError("Custom period requires a start")
            return cls(kind, start, end)
        return cls(kind, end - _SPANS[kind], end)

    def previous(self) -> Period:
        """The equally-long window immediately before this one (for trends)."""
        span = self.end - self.start
        return Period(self.kind, self.start - span, self.start)

    @property
    def label(self) -> str:
        return f"{self.start.isoformat()} — {self.end.isoformat()}"
