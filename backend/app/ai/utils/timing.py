"""Small timing helper for measuring AI processing duration (stage §8)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass(slots=True)
class Stopwatch:
    """Measures elapsed wall-clock time in milliseconds."""

    _start: float = field(default_factory=time.perf_counter)

    def elapsed_ms(self) -> int:
        return max(0, int((time.perf_counter() - self._start) * 1000))
