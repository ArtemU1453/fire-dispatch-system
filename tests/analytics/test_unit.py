"""Unit tests for analytics primitives (no database)."""

from __future__ import annotations

import io
import zipfile
from datetime import UTC, datetime

from app.analytics.export import ExportFormat, TableData, render
from app.analytics.kpi import DEFAULT_KPIS, KPI, KPIRegistry
from app.analytics.services.decision_support import _overloaded
from app.analytics.services.trends_service import _direction
from app.analytics.utils.cache import TTLCache
from app.analytics.utils.period import Period, PeriodKind


# ------------------------------------------------------------------ period ---
def test_period_windows() -> None:
    day = Period.of(PeriodKind.DAY)
    assert (day.end - day.start).days == 1
    week = Period.of(PeriodKind.WEEK)
    assert (week.end - week.start).days == 7
    prev = day.previous()
    assert prev.end == day.start
    assert (prev.end - prev.start) == (day.end - day.start)


def test_custom_period_requires_start() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 8, tzinfo=UTC)
    p = Period.of(PeriodKind.CUSTOM, start=start, end=end)
    assert p.start == start and p.end == end


# ------------------------------------------------------------- KPI registry ---
def test_kpi_registry_has_required_kpis() -> None:
    keys = set(DEFAULT_KPIS.keys())
    assert {
        "calls_total", "incidents_total", "avg_call_registration_seconds",
        "avg_decision_seconds", "avg_assignment_seconds", "avg_eta_seconds",
        "dispatcher_load", "unit_load", "resource_utilization_pct",
        "confirmed_recommendations_pct",
    } <= keys


def test_kpi_registry_is_extensible() -> None:
    reg = KPIRegistry()
    assert reg.all() == []

    async def _compute(_repo, _period):
        return 42.0

    reg.register(KPI("custom", "Custom", "u", _compute))
    assert reg.get("custom") is not None
    assert "custom" in reg.keys()


# ------------------------------------------------------------------ trends ---
def test_trend_direction() -> None:
    assert _direction(100, 50)[0] == "up"
    assert _direction(50, 100)[0] == "down"
    assert _direction(100, 100)[0] == "flat"
    assert _direction(None, 5)[0] == "n/a"
    assert _direction(100, 50)[1] == 100.0


# -------------------------------------------------------- decision support ---
def test_overloaded_detection() -> None:
    rows = [("A", 30), ("B", 3), ("C", 2)]
    over = _overloaded(rows, factor=2.0, floor=5)
    assert over == [("A", 30)]  # A is > 2x mean and above the floor


# ------------------------------------------------------------------- cache ---
def test_ttl_cache_stores_and_expires() -> None:
    cache = TTLCache(ttl_seconds=0.0)
    cache.set("k", 1)
    # ttl 0 → immediately expired
    assert cache.get("k") is None
    cache2 = TTLCache(ttl_seconds=100)
    cache2.set("k", 5)
    assert cache2.get("k") == 5


# ------------------------------------------------------------------ export ---
def test_csv_export() -> None:
    table = TableData(title="T", columns=["A", "B"], rows=[["Пожар", 42], ["x", None]])
    data = render(table, ExportFormat.CSV)
    assert data.startswith(b"\xef\xbb\xbf")  # UTF-8 BOM
    text = data.decode("utf-8")
    assert "Пожар" in text and "42" in text


def test_xlsx_export_is_valid_zip() -> None:
    table = TableData(title="T", columns=["KPI", "Знач"], rows=[["Вызовы", 3]])
    data = render(table, ExportFormat.XLSX)
    zf = zipfile.ZipFile(io.BytesIO(data))
    assert zf.testzip() is None
    assert "xl/worksheets/sheet1.xml" in zf.namelist()
    sheet = zf.read("xl/worksheets/sheet1.xml").decode("utf-8")
    assert "Вызовы" in sheet and "<v>3</v>" in sheet
