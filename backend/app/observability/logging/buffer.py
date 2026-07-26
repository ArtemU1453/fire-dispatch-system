"""In-memory capture of recent structured log records (stage §4, §7).

A :class:`logging.Handler` that records the last N log entries (with the current
Trace ID and masked contextual fields) so ``GET /observability/logs`` can return
them. A companion filter stamps every log record with the current Trace ID, so
existing loggers gain correlation without any change to their call sites.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.observability.tracing import get_trace_id
from app.observability.utils.masking import mask_value
from app.observability.utils.ring_buffer import RingBuffer

# Reserved LogRecord attributes that are not "extra" contextual fields.
_RESERVED = set(
    logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys()
) | {"message", "asctime", "taskName"}


@dataclass(slots=True)
class LogEntry:
    timestamp: datetime
    level: str
    logger: str
    message: str
    trace_id: str | None = None
    fields: dict[str, Any] = field(default_factory=dict)


class TraceIdFilter(logging.Filter):
    """Attach the current Trace ID to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not getattr(record, "trace_id", None):
            record.trace_id = get_trace_id()
        return True


class LogBuffer(logging.Handler):
    """A logging handler that keeps recent entries in a ring buffer."""

    def __init__(self, maxlen: int = 1000) -> None:
        super().__init__()
        self._entries: RingBuffer[LogEntry] = RingBuffer(maxlen=maxlen)
        self.addFilter(TraceIdFilter())

    def emit(self, record: logging.LogRecord) -> None:
        try:
            fields = {
                key: mask_value(key, value)
                for key, value in record.__dict__.items()
                if key not in _RESERVED
                and not key.startswith("_")
                and key != "trace_id"
            }
            self._entries.append(
                LogEntry(
                    timestamp=datetime.fromtimestamp(record.created, tz=UTC),
                    level=record.levelname,
                    logger=record.name,
                    message=record.getMessage(),
                    trace_id=getattr(record, "trace_id", None),
                    fields=fields,
                )
            )
        except Exception:  # pragma: no cover - logging must never raise
            self.handleError(record)

    def recent(
        self, *, limit: int = 100, level: str | None = None,
        trace_id: str | None = None,
    ) -> list[LogEntry]:
        entries = self._entries.snapshot()
        if level:
            entries = [e for e in entries if e.level == level.upper()]
        if trace_id:
            entries = [e for e in entries if e.trace_id == trace_id]
        return entries[:limit]

    def clear(self) -> None:
        self._entries.clear()
