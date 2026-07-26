"""In-memory recorder of recent request traces."""

from __future__ import annotations

from app.observability.tracing.context import TraceSpan
from app.observability.utils.ring_buffer import RingBuffer


class TraceRecorder:
    """Keeps the last N request spans for the traces dashboard."""

    def __init__(self, maxlen: int = 500) -> None:
        self._spans: RingBuffer[TraceSpan] = RingBuffer(maxlen=maxlen)

    def record(self, span: TraceSpan) -> None:
        self._spans.append(span)

    def recent(self, *, limit: int = 100) -> list[TraceSpan]:
        return self._spans.snapshot(limit=limit)

    def clear(self) -> None:
        self._spans.clear()
