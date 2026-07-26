"""The built-in KPIs registered into the default registry (stage §3).

Adding a KPI elsewhere is a one-liner: ``DEFAULT_KPIS.register(KPI(...))`` in any
module — nothing here needs to change.
"""

from __future__ import annotations

from app.analytics.kpi.base import KPI, KPIRegistry
from app.analytics.repositories.analytics_repository import AnalyticsRepository
from app.analytics.utils.period import Period

DEFAULT_KPIS = KPIRegistry()


async def _avg_eta(repo: AnalyticsRepository, period: Period) -> float | None:
    # Routing ETA is computed on demand and not persisted, so it is reported as
    # unavailable here rather than fabricated (no forecasting — stage constraint).
    return None


for _kpi in (
    KPI("calls_total", "Количество вызовов", "count",
        lambda r, p: r.call_count(p), category="volume",
        description="Число зарегистрированных вызовов за период"),
    KPI("incidents_total", "Количество происшествий", "count",
        lambda r, p: r.incident_count(p), category="volume",
        description="Число зарегистрированных происшествий за период"),
    KPI("avg_call_registration_seconds", "Среднее время регистрации вызова", "s",
        lambda r, p: r.avg_call_registration_seconds(p), category="time",
        description="Среднее время от поступления до ответа на вызов"),
    KPI("avg_decision_seconds", "Среднее время принятия решения", "s",
        lambda r, p: r.avg_decision_seconds(p), category="time",
        description="Среднее время от регистрации до подтверждения происшествия"),
    KPI("avg_assignment_seconds", "Среднее время назначения подразделений", "s",
        lambda r, p: r.avg_assignment_seconds(p), category="time",
        description="Среднее время от регистрации до назначения первого подразделения"),
    KPI("avg_eta_seconds", "Среднее расчётное время прибытия", "s",
        _avg_eta, category="time",
        description="Недоступно на этом этапе (маршрутные ETA не сохраняются)"),
    KPI("dispatcher_load", "Нагрузка на диспетчеров", "calls/dispatcher",
        lambda r, p: r.dispatcher_load(p), category="load",
        description="Среднее число вызовов на одного диспетчера"),
    KPI("unit_load", "Нагрузка на подразделения", "assign/unit",
        lambda r, p: r.unit_load(p), category="load",
        description="Среднее число назначений на одно подразделение"),
    KPI("resource_utilization_pct", "Процент использования ресурсов", "%",
        lambda r, p: r.resource_utilization_pct(p), category="load",
        description="Доля подразделений, недоступных для высылки (срез)"),
    KPI("confirmed_recommendations_pct",
        "Процент подтверждённых рекомендаций", "%",
        lambda r, p: r.confirmed_recommendations_pct(p), category="quality",
        description="Доля рекомендованных происшествий, приведших к высылке"),
):
    DEFAULT_KPIS.register(_kpi)
