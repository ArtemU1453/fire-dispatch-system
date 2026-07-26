"""Analytical dashboards (per role)."""

from __future__ import annotations

from app.analytics.dashboards.policy import (
    SPECS,
    DashboardRole,
    DashboardSpec,
    spec_for,
)
from app.analytics.dashboards.service import DashboardResult, DashboardService

__all__ = [
    "SPECS",
    "DashboardResult",
    "DashboardRole",
    "DashboardService",
    "DashboardSpec",
    "spec_for",
]
