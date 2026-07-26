"""API tests for the mobile BFF (Stage 19)."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio

CMD = "/api/v1/mobile/commander"
RESP = "/api/v1/mobile/responder"
BASE = "/api/v1/mobile"


# --------------------------------------------------------------- commander ---
async def test_commander_dashboard(client) -> None:
    r = await client.get(f"{CMD}/dashboard")
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["active_incidents"] == 2
    assert len(body["critical"]) >= 1


async def test_commander_incidents_resources_map(client) -> None:
    assert (await client.get(f"{CMD}/incidents")).status_code == 200
    assert len((await client.get(f"{CMD}/resources")).json()) == 3
    m = (await client.get(f"{CMD}/map")).json()
    assert m["incidents"] and m["units"]


async def test_commander_notes(client) -> None:
    r = await client.post(
        f"{CMD}/notes", json={"author": "chief", "text": "Замечание", "kind": "comment"}
    )
    assert r.status_code == 201
    assert r.json()["kind"] == "comment"
    r = await client.post(f"{CMD}/notes", json={"text": "   "})
    assert r.status_code == 422


# --------------------------------------------------------------- responder ---
async def test_responder_dispatch_and_route(client) -> None:
    r = await client.get(f"{RESP}/dispatch?unit_id=U1")
    assert r.status_code == 200
    assert r.json()["incident_id"] == "INC-1001"
    assert r.json()["current_status"] == "assigned"
    assert (await client.get(f"{RESP}/route?unit_id=U1")).status_code == 200
    assert (await client.get(f"{RESP}/dispatch?unit_id=NOPE")).status_code == 404


async def test_responder_status_flow_and_invalid(client) -> None:
    ok = await client.patch(
        f"{RESP}/status", json={"unit_id": "U1", "status": "en_route"}
    )
    assert ok.status_code == 200 and ok.json()["status"] == "en_route"
    bad = await client.patch(
        f"{RESP}/status", json={"unit_id": "U1", "status": "assigned"}
    )
    assert bad.status_code == 409                    # invalid transition
    unknown = await client.patch(
        f"{RESP}/status", json={"unit_id": "U1", "status": "flying"}
    )
    assert unknown.status_code == 422                # unknown status value


async def test_responder_message(client) -> None:
    r = await client.post(
        f"{RESP}/message",
        json={"unit_id": "U1", "text": "На месте", "incident_id": "INC-1001"},
    )
    assert r.status_code == 201 and r.json()["text"] == "На месте"
    assert (
        await client.post(f"{RESP}/message", json={"unit_id": "U1", "text": " "})
    ).status_code == 422


# ---------------------------------------------------------------- push/sync ---
async def test_device_register_and_unregister(client) -> None:
    r = await client.post(
        f"{BASE}/devices",
        json={"token": "d1", "user_id": "cmd", "app": "commander"},
    )
    assert r.status_code == 201 and r.json()["registered"] is True
    r = await client.request("DELETE", f"{BASE}/devices/d1")
    assert r.status_code == 200 and r.json()["unregistered"] is True


async def test_offline_sync_idempotent_endpoint(client) -> None:
    ops = {
        "operations": [
            {"op_id": "a1", "type": "status",
             "payload": {"unit_id": "U1", "status": "en_route"}},
            {"op_id": "a1", "type": "status", "payload": {}},   # replay
        ]
    }
    r = await client.post(f"{BASE}/sync", json=ops)
    assert r.status_code == 200
    results = r.json()["results"]
    assert results[0]["applied"] is True and results[0]["duplicate"] is False
    assert results[1]["duplicate"] is True


async def test_sync_applies_status_server_side(client) -> None:
    """Offline-queued status change is applied by the server, not the app."""
    r = await client.post(
        f"{BASE}/sync",
        json={"operations": [
            {"op_id": "s1", "type": "status",
             "payload": {"unit_id": "U1", "status": "en_route"}}
        ]},
    )
    assert r.json()["results"][0]["applied"] is True
    # The server now reports the new status on the dispatch card.
    card = (await client.get(f"{RESP}/dispatch?unit_id=U1")).json()
    assert card["current_status"] == "en_route"
