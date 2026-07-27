"""API + scenario tests for the Crisis Management Platform (PostgreSQL, §15).

Cover: operation creation, headquarters, sectors, resource management, plan &
tasks, the immutable journal/timeline, situation board, and RBAC access control.
Skip automatically when no database is reachable.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from tests.crisis.conftest import PREFIX

pytestmark = pytest.mark.asyncio

C = "/api/v1/crisis"


async def _new_operation(client, suffix: str = "01") -> str:
    r = await client.post(
        f"{C}/operations",
        json={
            "name": f"Крупный пожар {suffix}",
            "code": f"{PREFIX}-{suffix}",
            "response_level_code": "emergency",
        },
        headers={"X-User-Ref": "operator-1"},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def test_levels_seeded(client) -> None:
    r = await client.get(f"{C}/levels")
    assert r.status_code == 200
    codes = {level["code"] for level in r.json()}
    assert {"routine", "heightened", "emergency", "large_scale"} <= codes


async def test_create_operation_creates_headquarters(client) -> None:
    op_id = await _new_operation(client)
    r = await client.get(f"{C}/{op_id}")
    assert r.status_code == 200
    assert r.json()["status"] == "planned"
    assert r.json()["response_level_id"] is not None
    hq = await client.get(f"{C}/{op_id}/headquarters")
    assert hq.status_code == 200
    assert hq.json()["operation_id"] == op_id


async def test_duplicate_code_conflicts(client) -> None:
    await _new_operation(client, "dup")
    r = await client.post(
        f"{C}/operations", json={"name": "x", "code": f"{PREFIX}-dup"}
    )
    assert r.status_code == 409


async def test_headquarters_command_and_decisions(client) -> None:
    op_id = await _new_operation(client, "hq")
    r = await client.post(
        f"{C}/{op_id}/command",
        json={"role": "commander", "user_ref": "u-rtp", "display_name": "РТП Иванов",
              "responsibilities": "Общее руководство"},
    )
    assert r.status_code == 201 and r.json()["role"] == "commander"
    await client.post(
        f"{C}/{op_id}/command",
        json={"role": "deputy", "user_ref": "u-dep", "display_name": "Зам. Петров"},
    )
    members = (await client.get(f"{C}/{op_id}/command")).json()
    assert len(members) == 2
    # bad role rejected
    bad = await client.post(
        f"{C}/{op_id}/command", json={"role": "king", "user_ref": "x"}
    )
    assert bad.status_code == 422
    # record a decision → appears in the timeline as kind=decision
    d = await client.post(
        f"{C}/{op_id}/decision",
        json={"decision": "Сосредоточить силы на участке 1", "rationale": "угроза"},
    )
    assert d.status_code == 201 and d.json()["kind"] == "decision"
    decisions = (await client.get(f"{C}/{op_id}/timeline?kind=decision")).json()
    assert len(decisions) == 1


async def test_sectors_and_zone(client) -> None:
    op_id = await _new_operation(client, "sec")
    r = await client.post(
        f"{C}/{op_id}/sector",
        json={"name": "Участок 1", "leader_ref": "u-rtp",
              "center_lat": 55.7, "center_lon": 37.6},
    )
    assert r.status_code == 201
    sector_id = r.json()["id"]
    assert r.json()["status"] == "forming"
    sectors = (await client.get(f"{C}/{op_id}/sectors")).json()
    assert len(sectors) == 1
    upd = await client.patch(
        f"{C}/sectors/{sector_id}",
        json={"status": "active", "situation": "Локализация"},
    )
    assert upd.status_code == 200 and upd.json()["status"] == "active"
    z = await client.post(
        f"{C}/{op_id}/zone",
        json={"label": "Очаг", "kind": "hot", "sector_id": sector_id},
    )
    assert z.status_code == 201 and z.json()["kind"] == "hot"


async def test_resource_group_membership_and_relocation(client) -> None:
    op_id = await _new_operation(client, "res")
    s1 = (await client.post(f"{C}/{op_id}/sector", json={"name": "У1"})).json()["id"]
    s2 = (await client.post(f"{C}/{op_id}/sector", json={"name": "У2"})).json()["id"]
    g = await client.post(
        f"{C}/{op_id}/resource-group",
        json={"name": "Группа 1", "purpose": "тушение", "sector_id": s1},
    )
    assert g.status_code == 201
    gid = g.json()["id"]
    m = await client.post(
        f"{C}/resource-groups/{gid}/members",
        json={"kind": "unit", "ref": "U-101", "label": "АЦ-1"},
    )
    assert m.status_code == 201
    bad = await client.post(
        f"{C}/resource-groups/{gid}/members", json={"kind": "spaceship", "ref": "x"}
    )
    assert bad.status_code == 422
    mv = await client.post(
        f"{C}/resource-groups/{gid}/relocate",
        json={"to_sector_id": s2, "note": "перегруппировка"},
    )
    assert mv.status_code == 201
    assert mv.json()["from_sector_id"] == s1 and mv.json()["to_sector_id"] == s2
    history = (await client.get(f"{C}/resource-groups/{gid}/history")).json()
    assert len(history) == 1


async def test_plan_stages_and_tasks(client) -> None:
    op_id = await _new_operation(client, "plan")
    stage = await client.post(
        f"{C}/{op_id}/plan/stages", json={"name": "Разведка", "position": 1}
    )
    assert stage.status_code == 201
    stage_id = stage.json()["id"]
    t = await client.post(
        f"{C}/{op_id}/tasks",
        json={"title": "Провести разведку", "stage_id": stage_id,
              "assignee_ref": "u-rtp"},
    )
    assert t.status_code == 201 and t.json()["status"] == "pending"
    task_id = t.json()["id"]
    tasks = (await client.get(f"{C}/{op_id}/tasks")).json()
    assert len(tasks) == 1
    done = await client.patch(f"{C}/tasks/{task_id}/status", json={"status": "done"})
    assert done.status_code == 200 and done.json()["status"] == "done"
    bad = await client.patch(f"{C}/tasks/{task_id}/status", json={"status": "flying"})
    assert bad.status_code == 422


async def test_reports_board_and_timeline(client) -> None:
    op_id = await _new_operation(client, "board")
    await client.post(f"{C}/{op_id}/sector", json={"name": "У1"})
    await client.post(
        f"{C}/{op_id}/reports",
        json={"summary": "Обстановка стабильная", "author_ref": "u-rtp"},
    )
    await client.post(
        f"{C}/{op_id}/orders", json={"number": "1", "text": "Приказ №1"}
    )
    board = await client.get(f"{C}/{op_id}/board")
    assert board.status_code == 200
    body = board.json()
    assert len(body["sectors"]) == 1
    assert body["latest_report"] is not None
    # timeline has at least the "operation created" action entry
    timeline = (await client.get(f"{C}/{op_id}/timeline")).json()
    assert any(e["message"].startswith("Создана операция") for e in timeline)


async def test_update_operation_status(client) -> None:
    op_id = await _new_operation(client, "upd")
    r = await client.patch(f"{C}/{op_id}", json={"status": "active"})
    assert r.status_code == 200 and r.json()["status"] == "active"
    closed = await client.patch(f"{C}/{op_id}", json={"status": "closed"})
    assert closed.json()["ended_at"] is not None
    bad = await client.patch(f"{C}/{op_id}", json={"status": "nonsense"})
    assert bad.status_code == 422


async def test_rbac_denies_unknown_user(client) -> None:
    """A supplied user id without crisis permissions is denied (§13)."""
    r = await client.post(
        f"{C}/operations",
        json={"name": "x", "code": f"{PREFIX}-rbac"},
        headers={"X-User-Id": str(uuid4())},
    )
    assert r.status_code == 403


async def test_missing_operation_404(client) -> None:
    assert (await client.get(f"{C}/{uuid4()}")).status_code == 404
