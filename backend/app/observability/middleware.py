"""Observability middleware — Trace ID propagation + request metrics/traces.

Assigns each request a **Trace ID** (reused from an inbound ``X-Trace-ID`` /
``X-Request-ID`` header or freshly generated), binds it to the request context so
every log line correlates, records request **metrics** (count, duration, errors)
and a **trace span**, and echoes the Trace ID back on the response. It touches no
business logic — it only observes.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.observability.state import metrics_registry, trace_recorder
from app.observability.tracing import (
    TRACE_ID_HEADER,
    TraceSpan,
    new_trace_id,
    reset_trace_id,
    set_trace_id,
)

_REQUEST_ID_HEADER = "X-Request-ID"


def _route_template(request: Request) -> str:
    """The matched route template (low cardinality), else the raw path."""
    route = request.scope.get("route")
    return getattr(route, "path", None) or request.url.path


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        trace_id = (
            request.headers.get(TRACE_ID_HEADER)
            or request.headers.get(_REQUEST_ID_HEADER)
            or new_trace_id()
        )
        token = set_trace_id(trace_id)
        request.state.trace_id = trace_id
        start = time.perf_counter()
        status_code = 500
        error: str | None = None
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as exc:  # noqa: BLE001 - observe then re-raise
            error = type(exc).__name__
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            path = _route_template(request)
            metrics_registry.inc(
                "http_requests_total", method=request.method,
                path=path, status=str(status_code),
            )
            metrics_registry.observe(
                "http_request_duration_ms", duration_ms, method=request.method,
            )
            if status_code >= 500:
                metrics_registry.inc("http_errors_total")
            trace_recorder.record(
                TraceSpan.create(
                    trace_id, request.method, path, status_code, duration_ms,
                    error=error,
                )
            )
            if "response" in locals():
                response.headers[TRACE_ID_HEADER] = trace_id
            reset_trace_id(token)
