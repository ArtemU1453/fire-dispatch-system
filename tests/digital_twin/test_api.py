"""API (integration) tests for the Digital Twin (Stage 18 §8, §11)."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


async def test_list_scenarios(client) -> None:
    r = await client.get("/api/v1/digital-twin/scenarios")
    assert r.status_code == 200
    ids = {s["id"] for s in r.json()}
    assert {"open-south-station", "close-east-station"} <= ids


async def test_scenario_detail_and_404(client) -> None:
    r = await client.get("/api/v1/digital-twin/scenarios/open-south-station")
    assert r.status_code == 200
    assert r.json()["modifications"][0]["type"] == "open_station"
    r = await client.get("/api/v1/digital-twin/scenarios/missing")
    assert r.status_code == 404


async def test_create_scenario_then_simulate(client) -> None:
    payload = {
        "id": "my-scenario",
        "title": "Custom",
        "modifications": [
            {"type": "open_station",
             "params": {"id": "SZ", "name": "Z", "x": 5, "y": 5}}
        ],
    }
    r = await client.post("/api/v1/digital-twin/scenarios", json=payload)
    assert r.status_code == 201
    r = await client.post(
        "/api/v1/digital-twin/simulate", json={"scenario_id": "my-scenario"}
    )
    assert r.status_code == 200
    assert "verdict" in r.json()["impact"]


async def test_baseline_and_scenario_coverage(client) -> None:
    base = (await client.get("/api/v1/digital-twin/coverage")).json()
    scen = (
        await client.get(
            "/api/v1/digital-twin/coverage?scenario_id=open-south-station"
        )
    ).json()
    assert scen["population_covered_pct"] > base["population_covered_pct"]
    assert base["grid_size"] > 0


async def test_simulate_and_results(client) -> None:
    r = await client.post(
        "/api/v1/digital-twin/simulate", json={"scenario_id": "open-south-station"}
    )
    assert r.status_code == 200
    result = r.json()
    assert result["impact"]["delta_population_pct"] > 0
    assert result["baseline"]["population_covered_pct"] >= 0
    rid = result["id"]
    all_results = (await client.get("/api/v1/digital-twin/results")).json()
    assert len(all_results) == 1
    one = (
        await client.get(f"/api/v1/digital-twin/results?result_id={rid}")
    ).json()
    assert len(one) == 1 and one[0]["id"] == rid


async def test_placements_ranked(client) -> None:
    r = await client.post(
        "/api/v1/digital-twin/placements",
        json={"candidates": [
            {"id": "A", "name": "Юг", "x": 13, "y": 5},
            {"id": "B", "name": "Угол", "x": 29, "y": 29},
        ]},
    )
    assert r.status_code == 200
    rows = r.json()
    assert rows[0]["delta_population_pct"] >= rows[1]["delta_population_pct"]


async def test_forecast(client) -> None:
    r = await client.post(
        "/api/v1/digital-twin/forecast",
        json={"horizon_years": 3, "call_growth_rate": 0.05},
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["calls_per_day"]) == 4
    assert body["calls_per_day"][-1]["value"] > body["calls_per_day"][0]["value"]


async def test_reports(client) -> None:
    r = await client.get("/api/v1/digital-twin/reports")
    assert r.status_code == 200
    body = r.json()
    assert body["coverage_map"]["cells"]
    assert len(body["scenario_comparison"]) == 4
    assert body["justification"]


async def test_reports_for_selected_scenarios(client) -> None:
    r = await client.get(
        "/api/v1/digital-twin/reports?scenario_id=open-south-station"
    )
    assert r.status_code == 200
    assert len(r.json()["scenario_comparison"]) == 1


async def test_error_paths(client) -> None:
    assert (await client.post(
        "/api/v1/digital-twin/simulate", json={"scenario_id": "nope"}
    )).status_code == 404
    assert (await client.get(
        "/api/v1/digital-twin/coverage?scenario_id=nope"
    )).status_code == 404


async def test_isolation_baseline_unchanged_by_simulation(client) -> None:
    """Simulating a scenario must not mutate the baseline model."""
    before = (await client.get("/api/v1/digital-twin/coverage")).json()
    # Run several scenarios, including ones that add/close stations.
    for sid in ("open-south-station", "close-east-station",
                "repair-and-roadworks"):
        await client.post("/api/v1/digital-twin/simulate", json={"scenario_id": sid})
    after = (await client.get("/api/v1/digital-twin/coverage")).json()
    # Baseline coverage is identical → the reference model was never modified.
    assert after == before
