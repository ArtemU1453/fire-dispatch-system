"""Dashboards.

The aggregation logic lives in ``services.dashboard_service`` (kept with the other
services); it is re-exported here to match the module layout and is the seam for
additional dashboards (per-module, KPI) in the next stage.
"""

from __future__ import annotations

from app.observability.services.dashboard_service import (
    DashboardService,
    DashboardSummary,
)

__all__ = ["DashboardService", "DashboardSummary"]
