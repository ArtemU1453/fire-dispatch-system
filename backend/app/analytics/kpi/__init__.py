"""KPI framework (extensible registry + built-in definitions)."""

from __future__ import annotations

from app.analytics.kpi.base import KPI, KPIRegistry, KPIValue
from app.analytics.kpi.definitions import DEFAULT_KPIS

__all__ = ["DEFAULT_KPIS", "KPI", "KPIRegistry", "KPIValue"]
