"""Scenario format (Stage 17 §8).

A scenario is a self-describing, serialisable training exercise. It carries a
description, learning objectives, the initial fleet, the timed event sequence,
the expected result and the evaluation criteria. Scenarios are stored as JSON
(see :mod:`app.simulator.scenarios.store`) so they can be authored, versioned,
recorded and replayed independently of the running system — and entirely
separately from the production database.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.simulator.engine.enums import SimulationMode

SCENARIO_FORMAT_VERSION = 1


@dataclass
class ScenarioUnit:
    id: str
    name: str
    category: str
    x: float
    y: float
    speed_kmh: float = 50.0


@dataclass
class ScenarioEvent:
    """A timed event: a serialisable form of a scheduled world event."""

    time_s: float
    type: str
    payload: dict[str, Any] = field(default_factory=dict)
    id: str = ""


@dataclass
class EvaluationCriteria:
    """Thresholds used to grade a session (§7)."""

    max_response_time_s: float = 120.0     # norm for an adequate dispatch
    min_correct_pct: float = 80.0          # % incidents correctly handled
    max_errors: int = 2                    # tolerated invalid/late actions
    max_decision_changes: int = 3          # tolerated reassignments
    pass_score: float = 70.0               # overall score needed to pass


@dataclass
class ExpectedResult:
    """What a good response looks like (§8)."""

    resolved_incidents: int = 0
    max_expired_incidents: int = 0
    notes: str = ""


@dataclass
class Scenario:
    id: str
    title: str
    description: str
    mode: str = SimulationMode.TRAINING.value
    objectives: list[str] = field(default_factory=list)
    seed: int = 0
    duration_s: float = 1800.0
    units: list[ScenarioUnit] = field(default_factory=list)
    events: list[ScenarioEvent] = field(default_factory=list)
    expected: ExpectedResult = field(default_factory=ExpectedResult)
    criteria: EvaluationCriteria = field(default_factory=EvaluationCriteria)
    format_version: int = SCENARIO_FORMAT_VERSION

    # -- serialisation -------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Scenario:
        return cls(
            id=str(data["id"]),
            title=str(data.get("title", data["id"])),
            description=str(data.get("description", "")),
            mode=str(data.get("mode", SimulationMode.TRAINING.value)),
            objectives=list(data.get("objectives", [])),
            seed=int(data.get("seed", 0)),
            duration_s=float(data.get("duration_s", 1800.0)),
            units=[ScenarioUnit(**u) for u in data.get("units", [])],
            events=[ScenarioEvent(**e) for e in data.get("events", [])],
            expected=ExpectedResult(**data.get("expected", {})),
            criteria=EvaluationCriteria(**data.get("criteria", {})),
            format_version=int(data.get("format_version", SCENARIO_FORMAT_VERSION)),
        )
