"""API tests for the analytics endpoints (require PostgreSQL)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from .conftest import PREFIX, AnalyticsSeed

pytestmark = pytest.mark.asyncio


def _kpi(body, key):
    return next(k for k in body["kpis"] if k["key"] == key)


async def test_kpi_endpoint(api_client: AsyncClient, seed: AnalyticsSeed) -> None:
    resp = await api_client.get("/api/v1/analytics/kpi", params={"period": "day"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["period"]["kind"] == "day"
    assert _kpi(body, "calls_total")["value"] == 3
    assert _kpi(body, "avg_call_registration_seconds")["value"] == 20


async def test_statistics_endpoint(
    api_client: AsyncClient, seed: AnalyticsSeed
) -> None:
    resp = await api_client.get("/api/v1/analytics/statistics")
    assert resp.status_code == 200
    body = resp.json()
    labels = {d["label"]: d["count"] for d in body["by_incident_type"]}
    assert labels.get(seed.incident_type_name) == 3


async def test_trends_endpoint(api_client: AsyncClient, seed: AnalyticsSeed) -> None:
    resp = await api_client.get("/api/v1/analytics/trends")
    assert resp.status_code == 200
    keys = {t["key"] for t in resp.json()["trends"]}
    assert "calls_total" in keys


async def test_dashboard_endpoint(
    api_client: AsyncClient, seed: AnalyticsSeed
) -> None:
    resp = await api_client.get("/api/v1/analytics/dashboard/shift_lead")
    assert resp.status_code == 200
    body = resp.json()
    assert body["role"] == "shift_lead"
    assert body["statistics"] is not None
    assert body["kpis"]


async def test_reports_endpoint(api_client: AsyncClient, seed: AnalyticsSeed) -> None:
    resp = await api_client.get(
        "/api/v1/analytics/reports", params={"period": "week"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["generated_at"]
    assert body["statistics"] is not None


async def test_decision_support_endpoint(
    api_client: AsyncClient, seed: AnalyticsSeed
) -> None:
    resp = await api_client.get("/api/v1/analytics/decision-support")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_export_csv_and_audit(
    api_client: AsyncClient, seed: AnalyticsSeed, pg_factory
) -> None:
    resp = await api_client.post(
        "/api/v1/analytics/export",
        json={"dataset": "kpi", "format": "csv", "period": "day",
              "actor_name": f"{PREFIX}-admin"},
    )
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert resp.content.startswith(b"\xef\xbb\xbf")
    assert "attachment" in resp.headers["content-disposition"]

    # the export is audited in the shared audit_logs
    async with pg_factory() as s:
        rows = (await s.execute(
            text(
                "SELECT changes FROM audit_logs WHERE entity_type = "
                "'analytics_export' AND (changes->>'_actor_name') LIKE :p"
            ),
            {"p": f"{PREFIX}%"},
        )).all()
    assert rows
    assert rows[0][0]["dataset"] == "kpi"


async def test_export_xlsx(api_client: AsyncClient, seed: AnalyticsSeed) -> None:
    resp = await api_client.post(
        "/api/v1/analytics/export",
        json={"dataset": "incident_types", "format": "xlsx", "period": "day"},
    )
    assert resp.status_code == 200
    assert "spreadsheetml" in resp.headers["content-type"]
    assert resp.content[:2] == b"PK"  # zip magic


async def test_rbac_denies_unpermitted_user(
    api_client: AsyncClient, seed: AnalyticsSeed
) -> None:
    # the seeded user has no roles/permissions → analytics.view denied
    resp = await api_client.get(
        "/api/v1/analytics/kpi", params={"actor_id": seed.user_id}
    )
    assert resp.status_code == 403


async def test_rbac_admin_dashboard_denied(
    api_client: AsyncClient, seed: AnalyticsSeed
) -> None:
    resp = await api_client.get(
        "/api/v1/analytics/dashboard/admin",
        params={"actor_id": seed.user_id},
    )
    assert resp.status_code == 403
    # without a user context it is accessible (no auth wired)
    ok = await api_client.get("/api/v1/analytics/dashboard/admin")
    assert ok.status_code == 200
