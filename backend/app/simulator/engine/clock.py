"""Simulation clock with speed control, pause and stepping (Stage 17 §5).

The clock models *simulated* time independently of wall-clock time, so a session
can be accelerated, slowed, single-stepped or paused. The engine advances the
clock explicitly (``advance``/``step``); a real-time driver can map wall-clock
deltas onto it via :meth:`tick`, scaled by ``speed``.
"""

from __future__ import annotations


class SimulationClock:
    def __init__(self, speed: float = 1.0, step_seconds: float = 10.0) -> None:
        self._time_s: float = 0.0
        self._speed: float = 1.0
        self._paused: bool = False
        self._step_seconds: float = step_seconds
        self.set_speed(speed)

    @property
    def time_s(self) -> float:
        return self._time_s

    @property
    def speed(self) -> float:
        return self._speed

    @property
    def paused(self) -> bool:
        return self._paused

    @property
    def step_seconds(self) -> float:
        return self._step_seconds

    def set_speed(self, speed: float) -> None:
        """Set the time-acceleration factor (>0). 2.0 = twice as fast."""
        if speed <= 0:
            raise ValueError("speed must be positive")
        self._speed = float(speed)

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def advance(self, sim_seconds: float) -> float:
        """Advance simulated time by an explicit amount; returns new time.

        Advancing is ignored while paused so a paused session's world is frozen.
        """
        if sim_seconds < 0:
            raise ValueError("cannot advance time backwards")
        if not self._paused:
            self._time_s += sim_seconds
        return self._time_s

    def step(self) -> float:
        """Advance by one fixed step (пошаговое воспроизведение)."""
        # Stepping is an explicit instructor action, so it works even if paused.
        self._time_s += self._step_seconds
        return self._time_s

    def tick(self, real_seconds: float) -> float:
        """Advance by wall-clock delta scaled by ``speed`` (real-time driver)."""
        return self.advance(real_seconds * self._speed)
