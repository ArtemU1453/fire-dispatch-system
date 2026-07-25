"""Integration tests for the dispatch API against PostGIS (skip if no DB)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

REF = {"latitude": 55.7539, "longitude": 37.6208}


async def test_recommend_fire_selects_and_covers(api_client: AsyncClient, seed) -> None:
    resp = await api_client.post(
        "/api/v1/dispatch/recommend", json={"incident_type": "fire", **REF}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["incident_name"] == "Пожар"
    # BUSY (not deployable) and FAR (>30 km) are excluded → 2 candidates.
    assert body["total_candidates"] == 2
    rec = body["recommendation"]
    names = [u["name"] for u in rec["primary_units"]]
    assert names[0] == "NEAR"  # nearest scores highest
    coverage = {c["code"]: c for c in rec["capability_coverage"]}
    assert coverage["fire_suppression"]["provided"] >= 2
    assert coverage["water_supply"]["satisfied"] is True
    assert rec["sufficient"] is True
    assert rec["primary_units"][0]["reasons"]


async def test_recommend_orders_by_score(api_client: AsyncClient, seed) -> None:
    resp = await api_client.post(
        "/api/v1/dispatch/recommend", json={"incident_type": "fire", **REF}
    )
    scores = [u["score"] for u in resp.json()["recommendation"]["primary_units"]]
    assert scores == sorted(scores, reverse=True)


async def test_excluded_statuses_not_recommended(api_client: AsyncClient, seed) -> None:
    resp = await api_client.post(
        "/api/v1/dispatch/recommend", json={"incident_type": "fire", **REF}
    )
    all_units = (
        resp.json()["recommendation"]["primary_units"]
        + resp.json()["recommendation"]["reserve_units"]
    )
    assert "BUSY" not in {u["name"] for u in all_units}


async def test_preview_has_no_reserves(api_client: AsyncClient, seed) -> None:
    resp = await api_client.post(
        "/api/v1/dispatch/preview", json={"incident_type": "fire", **REF}
    )
    rec = resp.json()["recommendation"]
    assert rec["is_preview"] is True
    assert rec["reserve_units"] == []


async def test_unknown_incident_type_422(api_client: AsyncClient, seed) -> None:
    resp = await api_client.post(
        "/api/v1/dispatch/recommend", json={"incident_type": "nope", **REF}
    )
    assert resp.status_code == 422


async def test_missing_location_422(api_client: AsyncClient, seed) -> None:
    resp = await api_client.post(
        "/api/v1/dispatch/recommend", json={"incident_type": "fire"}
    )
    assert resp.status_code == 422


async def test_address_is_geocoded(api_client: AsyncClient, seed) -> None:
    # FakeGeoProvider resolves this to Red Square (Moscow), near the seeded units.
    resp = await api_client.post(
        "/api/v1/dispatch/recommend",
        json={"incident_type": "fire", "address": "Красная площадь, Москва"},
    )
    assert resp.status_code == 200
    assert resp.json()["recommendation"]["primary_units"]


async def test_rules_endpoint(api_client: AsyncClient, seed) -> None:
    resp = await api_client.get("/api/v1/dispatch/rules")
    assert resp.status_code == 200
    codes = {r["code"] for r in resp.json()}
    assert {"fire", "dtp", "gas_leak"} <= codes


async def test_capabilities_endpoint(api_client: AsyncClient, seed) -> None:
    resp = await api_client.get("/api/v1/dispatch/capabilities")
    assert resp.status_code == 200
    assert {"fire_suppression", "water_supply"} <= {c["code"] for c in resp.json()}
