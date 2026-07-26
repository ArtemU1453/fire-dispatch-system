"""Process-wide observability singletons.

Metrics, traces, logs and alerts are collected in-process (backend-agnostic, no
external system). These singletons are shared by the middleware (which records)
and the services / API (which read). ``install()`` wires the log buffer and
Trace-ID filter onto the root logger exactly once.
"""

from __future__ import annotations

import logging
import time

from app.observability.alerts import AlertRegistry
from app.observability.logging.buffer import LogBuffer, TraceIdFilter
from app.observability.metrics import MetricsRegistry
from app.observability.tracing import TraceRecorder

# The moment the process started — used for uptime.
START_TIME = time.time()

metrics_registry = MetricsRegistry()
trace_recorder = TraceRecorder()
log_buffer = LogBuffer()
alert_registry = AlertRegistry()

def install() -> None:
    """Attach the log buffer + Trace-ID filter to the root logger.

    Idempotent and safe to call from every ``create_app`` — ``configure_logging``
    clears root handlers, so this re-adds the buffer whenever it is missing.
    """
    root = logging.getLogger()
    if not any(isinstance(f, TraceIdFilter) for f in root.filters):
        root.addFilter(TraceIdFilter())
    if log_buffer not in root.handlers:
        root.addHandler(log_buffer)


def uptime_seconds() -> float:
    return round(time.time() - START_TIME, 3)
