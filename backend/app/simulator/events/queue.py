"""Time-ordered event queue (Stage 17)."""

from __future__ import annotations

import heapq
from collections.abc import Iterable

from app.simulator.events.definitions import ScheduledEvent


class EventQueue:
    """A min-heap of :class:`ScheduledEvent` ordered by simulated time.

    Insertion order breaks ties deterministically, so a scenario always replays
    identically.
    """

    def __init__(self, events: Iterable[ScheduledEvent] | None = None) -> None:
        self._heap: list[ScheduledEvent] = []
        self._seq: int = 0
        for ev in events or ():
            self.push(ev)

    def __len__(self) -> int:
        return len(self._heap)

    def push(self, event: ScheduledEvent) -> None:
        event.seq = self._seq
        self._seq += 1
        heapq.heappush(self._heap, event)

    def peek_time(self) -> float | None:
        """Sim time of the next event, or ``None`` if the queue is empty."""
        return self._heap[0].time_s if self._heap else None

    def pop_due(self, up_to_time_s: float) -> list[ScheduledEvent]:
        """Pop and return all events with ``time_s <= up_to_time_s`` in order."""
        due: list[ScheduledEvent] = []
        while self._heap and self._heap[0].time_s <= up_to_time_s:
            due.append(heapq.heappop(self._heap))
        return due

    def is_empty(self) -> bool:
        return not self._heap
