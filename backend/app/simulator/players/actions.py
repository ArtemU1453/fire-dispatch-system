"""Trainee actions and their recording (Stage 17 §6, §7).

Every decision a trainee dispatcher makes is captured as an immutable record
with the simulated time it occurred, so the evaluator can score reaction time,
correctness and the number of decision changes afterwards.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.simulator.engine.enums import ActionType


@dataclass(frozen=True)
class ActionRecord:
    """One recorded trainee action."""

    seq: int
    time_s: float
    type: ActionType
    incident_id: str | None = None
    unit_ids: tuple[str, ...] = field(default_factory=tuple)
    note: str = ""


@dataclass
class ActionOutcome:
    """The immediate result of applying an action to the world."""

    accepted: bool
    message: str = ""
    incident_id: str | None = None
