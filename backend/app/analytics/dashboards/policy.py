"""Role-based dashboard specifications (stage §4, §11).

Each role sees its own set of KPIs and sections. The ``required_permission`` is
enforced by the RBAC guard when a user is identified.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DashboardRole(str, Enum):
    SHIFT_LEAD = "shift_lead"          # Руководитель смены
    GARRISON_CHIEF = "garrison_chief"  # Начальник гарнизона
    ADMIN = "admin"                    # Администратор системы
    DISPATCHER = "dispatcher"          # Диспетчер


@dataclass(slots=True)
class DashboardSpec:
    role: DashboardRole
    title: str
    kpi_keys: list[str]
    include_statistics: bool = True
    include_findings: bool = True
    include_trends: bool = False
    required_permission: str = "analytics.view"


SPECS: dict[DashboardRole, DashboardSpec] = {
    DashboardRole.SHIFT_LEAD: DashboardSpec(
        role=DashboardRole.SHIFT_LEAD,
        title="Руководитель смены",
        kpi_keys=[
            "calls_total", "incidents_total",
            "avg_call_registration_seconds", "avg_decision_seconds",
            "dispatcher_load", "unit_load", "confirmed_recommendations_pct",
        ],
        include_statistics=True, include_findings=True,
    ),
    DashboardRole.GARRISON_CHIEF: DashboardSpec(
        role=DashboardRole.GARRISON_CHIEF,
        title="Начальник гарнизона",
        kpi_keys=[
            "incidents_total", "avg_assignment_seconds", "unit_load",
            "resource_utilization_pct", "confirmed_recommendations_pct",
        ],
        include_statistics=True, include_findings=True, include_trends=True,
    ),
    DashboardRole.ADMIN: DashboardSpec(
        role=DashboardRole.ADMIN,
        title="Администратор системы",
        kpi_keys=[],  # empty = all KPIs
        include_statistics=True, include_findings=True, include_trends=True,
        required_permission="analytics.admin",
    ),
    DashboardRole.DISPATCHER: DashboardSpec(
        role=DashboardRole.DISPATCHER,
        title="Диспетчер",
        kpi_keys=[
            "calls_total", "incidents_total",
            "avg_call_registration_seconds", "dispatcher_load",
            "confirmed_recommendations_pct",
        ],
        include_statistics=False, include_findings=False,
    ),
}


def spec_for(role: DashboardRole) -> DashboardSpec:
    return SPECS[role]
