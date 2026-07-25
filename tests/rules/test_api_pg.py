"""End-to-end API tests for the rules infrastructure (PostgreSQL).

Covers the full lifecycle through the REST surface: creation + publishing,
retrieval, versioning (a new version supersedes the active one), ready-made
requirements, category filtering, incident-type resolution, publish-time
validation and soft deletion.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from .conftest import RulesSeed, rule_payload

pytestmark = pytest.mark.asyncio


async def test_create_publish_and_get(api_client: AsyncClient, seed: RulesSeed) -> None:
    code = f"{seed.prefix}-API1"
    resp = await api_client.post("/api/v1/rules", json=rule_payload(seed, code=code))
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["code"] == code
    assert body["active_version"]["version_number"] == 1
    assert body["active_version"]["status"] == "published"
    assert body["active_version"]["is_active"] is True
    assert sorted(body["tags"]) == ["building", "fire"]

    rule_id = body["id"]
    got = await api_client.get(f"/api/v1/rules/{rule_id}")
    assert got.status_code == 200
    assert got.json()["active_version"]["priority"] == "high"


async def test_versioning_supersedes_active_version(
    api_client: AsyncClient, seed: RulesSeed
) -> None:
    code = f"{seed.prefix}-API2"
    created = await api_client.post(
        "/api/v1/rules", json=rule_payload(seed, code=code)
    )
    rule_id = created.json()["id"]

    # Add and publish a second version.
    update = {
        "new_version": {
            "priority": "critical",
            "actions": [{"action_type": "require_resources", "sort_order": 0}],
            "resource_requirements": [
                {"resource_category": "vehicle", "min_count": 3, "recommended_count": 4}
            ],
            "capability_requirements": [],
        },
        "publish": True,
    }
    resp = await api_client.put(f"/api/v1/rules/{rule_id}", json=update)
    assert resp.status_code == 200, resp.text
    active = resp.json()["active_version"]
    assert active["version_number"] == 2
    assert active["priority"] == "critical"

    # All versions are retained; only one is active.
    versions = (await api_client.get(f"/api/v1/rules/versions/{rule_id}")).json()
    assert {v["version_number"] for v in versions} == {1, 2}
    assert [v for v in versions if v["is_active"]][0]["version_number"] == 2
    statuses = {v["version_number"]: v["status"] for v in versions}
    assert statuses[1] == "archived"
    assert statuses[2] == "published"


async def test_requirements_endpoint(
    api_client: AsyncClient, seed: RulesSeed
) -> None:
    code = f"{seed.prefix}-API3"
    created = await api_client.post(
        "/api/v1/rules", json=rule_payload(seed, code=code)
    )
    rule_id = created.json()["id"]

    resp = await api_client.get(f"/api/v1/rules/{rule_id}/requirements")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["rule_code"] == code
    assert body["version_number"] == 1
    minimum = {c["resource_category"]: c["count"] for c in body["minimum_composition"]}
    assert minimum["vehicle"] == 2
    assert body["required_capabilities"] == ["fire_suppression"]


async def test_incident_type_resolution(
    api_client: AsyncClient, seed: RulesSeed
) -> None:
    code = f"{seed.prefix}-API4"
    await api_client.post("/api/v1/rules", json=rule_payload(seed, code=code))

    resp = await api_client.get(f"/api/v1/rules/incident/{seed.incident_type_id}")
    assert resp.status_code == 200, resp.text
    codes = {r["code"] for r in resp.json()}
    assert code in codes


async def test_category_filter(api_client: AsyncClient, seed: RulesSeed) -> None:
    code = f"{seed.prefix}-API5"
    await api_client.post("/api/v1/rules", json=rule_payload(seed, code=code))

    in_cat = await api_client.get(f"/api/v1/rules/category/{seed.category_id}")
    assert code in {r["code"] for r in in_cat.json()}

    other = await api_client.get(f"/api/v1/rules/category/{seed.other_category_id}")
    assert code not in {r["code"] for r in other.json()}


async def test_publish_validation_rejects_empty_version(
    api_client: AsyncClient, seed: RulesSeed
) -> None:
    payload = rule_payload(seed, code=f"{seed.prefix}-API6")
    payload["version"]["actions"] = []
    payload["version"]["resource_requirements"] = []
    payload["version"]["capability_requirements"] = []
    resp = await api_client.post("/api/v1/rules", json=payload)
    assert resp.status_code == 422
    assert "at least one requirement or action" in resp.text


async def test_duplicate_code_conflicts(
    api_client: AsyncClient, seed: RulesSeed
) -> None:
    code = f"{seed.prefix}-API7"
    first = await api_client.post("/api/v1/rules", json=rule_payload(seed, code=code))
    assert first.status_code == 201
    dup = await api_client.post("/api/v1/rules", json=rule_payload(seed, code=code))
    assert dup.status_code == 409


async def test_soft_delete(api_client: AsyncClient, seed: RulesSeed) -> None:
    code = f"{seed.prefix}-API8"
    created = await api_client.post(
        "/api/v1/rules", json=rule_payload(seed, code=code)
    )
    rule_id = created.json()["id"]

    deleted = await api_client.delete(f"/api/v1/rules/{rule_id}")
    assert deleted.status_code == 204
    missing = await api_client.get(f"/api/v1/rules/{rule_id}")
    assert missing.status_code == 404
