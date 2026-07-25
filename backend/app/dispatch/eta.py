"""ETA seam — interface only (routing is a later stage).

The Dispatch Engine must eventually obtain an estimated time of arrival from a
dedicated routing service. This stage defines only the :class:`ETAProvider`
interface and a null implementation; no routing, distance-over-roads or traffic
logic exists yet. The scorer includes an arrival sub-score **only** when a
provider returns a value, so plugging a real ETA service in later needs no change
to the scoring or engine code.
"""

from __future__ import annotations

from typing import Protocol


class ETAProvider(Protocol):
    """Estimates arrival time (seconds) for a candidate a given distance away.

    Returns ``None`` when unknown. The next stage will provide a real
    implementation (routing / traffic); until then only :class:`NullETAProvider`
    is wired in.
    """

    def estimate(self, distance_meters: float | None) -> float | None: ...


class NullETAProvider:
    """Default provider — no ETA yet (routing is a later stage)."""

    def estimate(self, distance_meters: float | None) -> float | None:
        return None
