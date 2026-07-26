"""Request tracing — correlation (Trace) IDs (stage §5).

Every request carries a unique **Trace ID** that flows through all internal
services via a :class:`contextvars.ContextVar`, so any log line or metric emitted
while handling a request can be correlated. This is transport- and
backend-agnostic: the same context can later feed OpenTelemetry without changing
callers.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import UTC, datetime

# The current request's Trace ID (None outside a request).
_trace_id: ContextVar[str | None] = ContextVar("trace_id", default=None)

TRACE_ID_HEADER = "X-Trace-ID"


def new_trace_id() -> str:
    return uuid.uuid4().hex


def get_trace_id() -> str | None:
    return _trace_id.get()


def set_trace_id(trace_id: str | None):
    """Bind ``trace_id`` to the current context; returns the reset token."""
    return _trace_id.set(trace_id)


def reset_trace_id(token) -> None:
    _trace_id.reset(token)


@dataclass(slots=True)
class TraceSpan:
    """A recorded request span (one per HTTP request)."""

    trace_id: str
    method: str
    path: str
    status_code: int
    duration_ms: float
    started_at: datetime
    error: str | None = None

    @classmethod
    def create(
        cls,
        trace_id: str,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        *,
        error: str | None = None,
    ) -> TraceSpan:
        return cls(
            trace_id=trace_id,
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=round(duration_ms, 2),
            started_at=datetime.now(tz=UTC),
            error=error,
        )
