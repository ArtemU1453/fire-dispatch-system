"""Offline synchronisation (Stage 19 §Offline).

Mobile apps queue user actions while offline and replay them on reconnect. To
make replay safe, each queued operation carries a client-generated idempotency
key; the server applies each key at most once and returns a per-operation
acknowledgement, so re-sending after a flaky connection never double-applies.

The apps hold the local cache and outbound queue; this server-side piece
guarantees idempotent, ordered application and reports what was applied.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SyncOperation:
    op_id: str                       # client-generated idempotency key
    type: str                        # e.g. "status" | "message"
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncResult:
    op_id: str
    applied: bool
    duplicate: bool = False
    error: str | None = None
    result: dict[str, Any] | None = None


# A handler applies one operation payload and returns a small result dict.
OpHandler = Callable[[dict[str, Any]], dict[str, Any]]


class SyncService:
    """Applies queued operations idempotently by op_id."""

    def __init__(self) -> None:
        self._handlers: dict[str, OpHandler] = {}
        self._applied: dict[str, SyncResult] = {}

    def register(self, op_type: str, handler: OpHandler) -> None:
        self._handlers[op_type] = handler

    def process(self, operations: list[SyncOperation]) -> list[SyncResult]:
        results: list[SyncResult] = []
        for op in operations:
            results.append(self._process_one(op))
        return results

    def _process_one(self, op: SyncOperation) -> SyncResult:
        prior = self._applied.get(op.op_id)
        if prior is not None:
            # Idempotent replay: report the original outcome, marked duplicate.
            return SyncResult(
                op_id=op.op_id,
                applied=prior.applied,
                duplicate=True,
                error=prior.error,
                result=prior.result,
            )
        handler = self._handlers.get(op.type)
        if handler is None:
            result = SyncResult(op.op_id, applied=False, error=f"unknown op: {op.type}")
            # Unknown ops are not memoised, so a fixed client can retry them.
            return result
        try:
            out = handler(op.payload)
            result = SyncResult(op.op_id, applied=True, result=out)
        except Exception as exc:  # noqa: BLE001 - report, don't crash the batch
            result = SyncResult(op.op_id, applied=False, error=str(exc))
        self._applied[op.op_id] = result
        return result
