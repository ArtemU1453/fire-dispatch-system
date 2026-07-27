"""Database-free unit tests for the Crisis Management Platform (Stage 20)."""

from __future__ import annotations

import pytest

from app.crisis.models.enums import (
    CommandRole,
    JournalKind,
    OperationStatus,
    ResourceMemberKind,
    SectorStatus,
    TaskStatus,
    values,
)
from app.crisis.services.access import (
    PERM_MANAGE,
    PERM_VIEW,
    CrisisAccess,
)
from app.crisis.services.journal import JournalService


def test_enum_vocabularies() -> None:
    assert "active" in values(OperationStatus)
    assert set(values(CommandRole)) == {"commander", "deputy"}
    assert "on_scene" not in values(TaskStatus)  # that belongs to responder
    assert values(TaskStatus) == ["pending", "in_progress", "done", "cancelled"]
    assert "forming" in values(SectorStatus)
    assert "decision" in values(JournalKind) and "action" in values(JournalKind)
    assert set(values(ResourceMemberKind)) == {"unit", "vehicle", "personnel"}


@pytest.mark.asyncio
async def test_access_is_open_when_no_user() -> None:
    # No session is touched when user_id is None (open access), so a dummy
    # session object is safe here.
    access = CrisisAccess(session=object())  # type: ignore[arg-type]
    await access.require(None, PERM_MANAGE)   # must not raise
    assert await access.can(None, PERM_VIEW) is True


def test_journal_is_append_only() -> None:
    # Immutability (§8): the journal service exposes append + reads only —
    # there is deliberately no update or delete method.
    assert hasattr(JournalService, "append")
    assert hasattr(JournalService, "timeline")
    assert not hasattr(JournalService, "update")
    assert not hasattr(JournalService, "delete")
