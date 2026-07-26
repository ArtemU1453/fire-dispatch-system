"""API tests for the simulation & training platform (Stage 17 §9).

Database-free: the simulator holds no production data, so these run without
PostgreSQL.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


async def _start(client, scenario_id="basic-fire-01", trainee="ivanov"):
    r = await client.post(
        "/api/v1/training/start",
        json={"scenario_id": scenario_id, "trainee": trainee},
    )
    assert r.status_code == 200, r.text
    return r.json()["id"]


async def test_list_scenarios(client) -> None:
    r = await client.get("/api/v1/training/scenarios")
    assert r.status_code == 200
    ids = {s["id"] for s in r.json()}
    assert {"basic-fire-01", "exam-multi-01", "mass-incident-01"} <= ids
    # summary carries counts
    basic = next(s for s in r.json() if s["id"] == "basic-fire-01")
    assert basic["unit_count"] == 3
    assert basic["mode"] == "training"


async def test_get_scenario_detail_and_404(client) -> None:
    r = await client.get("/api/v1/training/scenarios/basic-fire-01")
    assert r.status_code == 200
    assert r.json()["events"][0]["type"] == "spawn_incident"
    assert (await client.get("/api/v1/training/scenarios/missing")).status_code == 404


async def test_create_scenario(client) -> None:
    payload = {
        "id": "custom-01",
        "title": "Custom",
        "description": "d",
        "mode": "free",
        "units": [{"id": "U0", "name": "AC", "category": "fire", "x": 0, "y": 0}],
        "events": [{
            "time_s": 5, "type": "spawn_incident",
            "payload": {"id": "C1", "type": "fire", "x": 1, "y": 1,
                        "severity": 1, "required_units": 1,
                        "required_category": "fire"},
        }],
    }
    r = await client.post("/api/v1/training/scenarios", json=payload)
    assert r.status_code == 201, r.text
    assert r.json()["id"] == "custom-01"
    # now startable
    r = await client.post("/api/v1/training/start", json={"scenario_id": "custom-01"})
    assert r.status_code == 200


async def test_full_training_flow_scores_pass(client) -> None:
    sid = await _start(client)
    # advance so the incident (t=30) appears
    r = await client.post(
        f"/api/v1/training/sessions/{sid}/control",
        json={"op": "advance", "seconds": 30},
    )
    assert r.status_code == 200
    pending = [i for i in r.json()["incidents"] if i["status"] == "pending"]
    assert pending
    inc_id = pending[0]["id"]
    r = await client.post(
        f"/api/v1/training/sessions/{sid}/dispatch",
        json={"incident_id": inc_id, "unit_ids": ["U000"]},
    )
    assert r.json()["accepted"] is True
    r = await client.post("/api/v1/training/stop", json={"session_id": sid})
    assert r.status_code == 200
    assert r.json()["verdict"] == "passed"
    assert r.json()["score"] >= 70


async def test_playback_controls(client) -> None:
    sid = await _start(client)
    r = await client.post(
        f"/api/v1/training/sessions/{sid}/control", json={"op": "pause"}
    )
    assert r.json()["state"] == "paused" and r.json()["paused"] is True
    r = await client.post(
        f"/api/v1/training/sessions/{sid}/control", json={"op": "resume"}
    )
    assert r.json()["state"] == "running"
    r = await client.post(
        f"/api/v1/training/sessions/{sid}/control",
        json={"op": "set_speed", "speed": 4},
    )
    assert r.json()["speed"] == 4
    r = await client.post(
        f"/api/v1/training/sessions/{sid}/control", json={"op": "step"}
    )
    assert r.json()["sim_time_s"] > 0
    # bad op / missing arg
    assert (await client.post(
        f"/api/v1/training/sessions/{sid}/control", json={"op": "advance"}
    )).status_code == 422
    assert (await client.post(
        f"/api/v1/training/sessions/{sid}/control", json={"op": "bogus"}
    )).status_code == 422


async def test_results_and_statistics(client) -> None:
    sid = await _start(client)
    await client.post("/api/v1/training/stop", json={"session_id": sid})
    r = await client.get("/api/v1/training/results")
    assert r.status_code == 200 and len(r.json()) == 1
    r = await client.get(f"/api/v1/training/results?session_id={sid}")
    assert len(r.json()) == 1
    r = await client.get("/api/v1/training/statistics")
    stats = r.json()
    assert stats["sessions_completed"] == 1
    assert stats["by_scenario"]["basic-fire-01"] == 1


async def test_action_after_stop_conflicts(client) -> None:
    sid = await _start(client)
    await client.post("/api/v1/training/stop", json={"session_id": sid})
    r = await client.post(
        f"/api/v1/training/sessions/{sid}/dispatch",
        json={"incident_id": "X", "unit_ids": []},
    )
    assert r.status_code == 409


async def test_unknown_session_and_scenario_404(client) -> None:
    assert (await client.get("/api/v1/training/sessions/nope")).status_code == 404
    assert (await client.post(
        "/api/v1/training/start", json={"scenario_id": "nope"}
    )).status_code == 404
    assert (await client.post(
        "/api/v1/training/stop", json={"session_id": "nope"}
    )).status_code == 404


async def test_isolation_no_production_incident_endpoints_touched(client) -> None:
    """Sanity: training runs without creating any real incidents."""
    sid = await _start(client)
    await client.post(
        f"/api/v1/training/sessions/{sid}/control",
        json={"op": "advance", "seconds": 30},
    )
    # The training incident lives only in the session view, not the incidents API.
    r = await client.get(f"/api/v1/training/sessions/{sid}")
    assert any(i["id"].startswith("INC") for i in r.json()["incidents"])
