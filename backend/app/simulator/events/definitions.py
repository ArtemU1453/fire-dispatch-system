"""Scheduled simulation events (Stage 17).

An event is a timestamped instruction applied to the world as the clock reaches
it: spawn an incident, break a unit, close a road, change the weather, etc. The
scenario is essentially an ordered list of these events plus initial state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.simulator.engine.enums import EventType


@dataclass(order=True)
class ScheduledEvent:
    """An event to apply at ``time_s`` of simulated time.

    ``order=True`` with the sort key first lets the event queue order events by
    time (ties broken by insertion sequence, assigned by the queue).
    """

    time_s: float
    seq: int = field(default=0)
    type: EventType = field(default=EventType.MESSAGE, compare=False)
    payload: dict[str, Any] = field(default_factory=dict, compare=False)
    id: str = field(default="", compare=False)
