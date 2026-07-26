"""Unit tests for the mobile BFF (Stage 19)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.mobile.providers.sample import SampleDataProvider
from app.mobile.push.base import Device, PushEventType
from app.mobile.push.providers import LogPushProvider
from app.mobile.push.service import PushService
from app.mobile.security.tokens import SessionExpiredError, SessionStore
from app.mobile.services.commander import CommanderService
from app.mobile.services.offline import SyncOperation, SyncService
from app.mobile.services.responder import ResponderError, ResponderService
from app.mobile.services.status import (
    InvalidStatusTransition,
    ResponderStateStore,
    ResponderStatus,
    can_transition,
)


# ---------------------------------------------------------------- provider ---
def test_sample_provider_shapes() -> None:
    p = SampleDataProvider()
    assert len(p.list_incidents(active_only=True)) == 2
    assert p.get_dispatch("U1") is not None
    assert p.get_dispatch("U2") is None       # no assignment
    summary = p.operational_summary()
    assert summary.busy_units == 1 and summary.available_units == 2


# --------------------------------------------------------------- commander ---
def test_commander_dashboard_and_critical() -> None:
    svc = CommanderService(SampleDataProvider())
    dash = svc.dashboard()
    assert dash.summary.active_incidents == 2
    # INC-1001 is high priority → a critical notification
    assert any(c.incident_id == "INC-1001" for c in dash.critical)
    m = svc.map_data()
    assert m["incidents"] and m["units"]


def test_commander_notes() -> None:
    svc = CommanderService(SampleDataProvider())
    note = svc.add_note(author="chief", text="Проверить гидранты", kind="comment")
    assert note.kind == "comment"
    assert svc.list_notes()[0].id == note.id


# ------------------------------------------------------------------ status ---
def test_status_transitions() -> None:
    assert can_transition(ResponderStatus.ASSIGNED, ResponderStatus.EN_ROUTE)
    assert not can_transition(ResponderStatus.ASSIGNED, ResponderStatus.WORKING)
    store = ResponderStateStore()
    assert store.current("U1") == ResponderStatus.ASSIGNED
    store.transition("U1", ResponderStatus.EN_ROUTE)
    store.transition("U1", ResponderStatus.ON_SCENE)
    with pytest.raises(InvalidStatusTransition):
        store.transition("U1", ResponderStatus.ASSIGNED)


# --------------------------------------------------------------- responder ---
def test_responder_dispatch_route_status_message() -> None:
    provider = SampleDataProvider()
    push = PushService(LogPushProvider())
    svc = ResponderService(provider, push=push)
    assert svc.dispatch("U1").incident_id == "INC-1001"
    assert len(svc.route("U1").points) == 2
    assert svc.update_status("U1", ResponderStatus.EN_ROUTE) == ResponderStatus.EN_ROUTE
    msg = svc.send_message("U1", from_user="U1", text="Прибыли")
    assert msg.text == "Прибыли"
    with pytest.raises(ResponderError):
        svc.dispatch("UNKNOWN")
    with pytest.raises(ResponderError):
        svc.send_message("U1", from_user="U1", text="  ")


# --------------------------------------------------------------------- push ---
def test_push_registry_and_events() -> None:
    provider = LogPushProvider()
    push = PushService(provider)
    push.register(Device(token="t1", user_id="cmd", app="commander"))
    push.register(Device(token="t2", user_id="u1", app="responder"))
    assert len(push.devices_for("cmd")) == 1
    n = push.notify_new_incident("INC-9", "Пожар", user_ids=["cmd"])
    assert n == 1
    push.notify_critical("Взрыв газа", incident_id="INC-9")
    events = {r.message["event"] for r in provider.sent}
    assert PushEventType.NEW_INCIDENT.value in events
    assert PushEventType.CRITICAL.value in events
    assert push.unregister("t1") is True


# ------------------------------------------------------------------ offline ---
def test_offline_sync_idempotent() -> None:
    sync = SyncService()
    calls: list[dict] = []
    sync.register("status", lambda p: (calls.append(p), {"ok": True})[1])
    ops = [
        SyncOperation("op1", "status", {"unit_id": "U1"}),
        SyncOperation("op1", "status", {"unit_id": "U1"}),   # duplicate
        SyncOperation("op2", "unknown", {}),                 # unknown handler
    ]
    results = sync.process(ops)
    assert results[0].applied and not results[0].duplicate
    assert results[1].duplicate is True
    assert results[2].applied is False
    assert len(calls) == 1                                   # applied once only


# ----------------------------------------------------------------- security ---
def test_session_store_idle_and_revoke() -> None:
    store = SessionStore(idle_ttl=timedelta(minutes=10))
    token = store.create("user-1", app="responder")
    # raw token is returned; only its hash is stored (not the token itself)
    assert all(token != s.token_hash for s in store.active_sessions("user-1"))
    now = datetime.now(tz=UTC)
    assert store.validate(token, now=now).user_id == "user-1"
    # idle beyond ttl → expired
    with pytest.raises(SessionExpiredError):
        store.validate(token, now=now + timedelta(minutes=11))


def test_session_remote_revoke_all() -> None:
    store = SessionStore()
    t1 = store.create("user-1")
    store.create("user-1")
    assert len(store.active_sessions("user-1")) == 2
    assert store.revoke_all_for_user("user-1") == 2
    with pytest.raises(SessionExpiredError):
        store.validate(t1)
