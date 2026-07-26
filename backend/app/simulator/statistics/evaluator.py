"""Trainee evaluation & statistics (Stage 17 §7).

Given a finished engine (its recorded actions and final world) and the scenario,
compute objective metrics: reaction time, correctness of unit selection,
compliance with the response-time norm, number of errors, number of decision
changes and overall accuracy — then an aggregate score and pass/fail verdict.
Purely descriptive arithmetic over recorded facts; no production data involved.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.simulator.engine.engine import Engine
from app.simulator.engine.enums import (
    ActionType,
    SimIncidentStatus,
    SimUnitCategory,
)
from app.simulator.scenarios.schema import Scenario


@dataclass
class IncidentEvaluation:
    incident_id: str
    is_false_alarm: bool
    reaction_time_s: float | None
    within_norm: bool
    correct: bool
    resolved: bool


@dataclass
class EvaluationResult:
    total_incidents: int = 0
    real_incidents: int = 0
    resolved_incidents: int = 0
    expired_incidents: int = 0
    correct_incidents: int = 0
    avg_reaction_time_s: float | None = None
    norm_compliance_pct: float = 0.0
    correct_pct: float = 0.0
    accuracy_pct: float = 0.0
    error_count: int = 0
    decision_changes: int = 0
    score: float = 0.0
    passed: bool = False
    per_incident: list[IncidentEvaluation] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {k: v for k, v in self.__dict__.items() if k != "per_incident"}
        d["per_incident"] = [ie.__dict__ for ie in self.per_incident]
        return d


def _first_dispatch(engine: Engine, incident_id: str) -> float | None:
    for a in engine.actions:
        if (
            a.incident_id == incident_id
            and a.type in (ActionType.DISPATCH, ActionType.REASSIGN)
            and not a.note.startswith("rejected")
        ):
            return a.time_s
    return None


def _units_ok(engine: Engine, incident, unit_ids: tuple[str, ...]) -> bool:
    matching = [
        u
        for uid in unit_ids
        if (u := engine.world.units.get(uid))
        and u.category == SimUnitCategory(incident.required_category)
    ]
    return len(matching) >= incident.required_units


def evaluate(engine: Engine, scenario: Scenario) -> EvaluationResult:
    result = EvaluationResult()
    incidents = list(engine.world.incidents.values())
    result.total_incidents = len(incidents)
    reactions: list[float] = []
    within_norm = 0

    for inc in incidents:
        first = _first_dispatch(engine, inc.id)
        reaction = (first - inc.created_at) if first is not None else None
        resolved = inc.status == SimIncidentStatus.RESOLVED
        if inc.status == SimIncidentStatus.EXPIRED:
            result.expired_incidents += 1

        if inc.is_false_alarm:
            # Correct handling of a false alarm = NOT dispatching real units.
            correct = first is None
            norm_ok = True
        else:
            result.real_incidents += 1
            dispatched_units = tuple(inc.dispatched_unit_ids)
            correct = resolved and _units_ok(engine, inc, dispatched_units)
            norm_ok = (
                reaction is not None
                and reaction <= scenario.criteria.max_response_time_s
            )
            if reaction is not None:
                reactions.append(reaction)
            if norm_ok:
                within_norm += 1

        if resolved:
            result.resolved_incidents += 1
        if correct:
            result.correct_incidents += 1
        result.per_incident.append(
            IncidentEvaluation(
                incident_id=inc.id,
                is_false_alarm=inc.is_false_alarm,
                reaction_time_s=round(reaction, 1) if reaction is not None else None,
                within_norm=norm_ok,
                correct=correct,
                resolved=resolved,
            )
        )

    # Aggregate metrics.
    result.decision_changes = sum(
        1 for a in engine.actions if a.type == ActionType.REASSIGN
    )
    rejected = sum(1 for a in engine.actions if a.note.startswith("rejected"))
    false_alarm_dispatches = sum(
        1
        for ie in result.per_incident
        if ie.is_false_alarm and ie.reaction_time_s is not None
    )
    result.error_count = rejected + false_alarm_dispatches + result.expired_incidents
    result.avg_reaction_time_s = (
        round(sum(reactions) / len(reactions), 1) if reactions else None
    )
    result.norm_compliance_pct = round(
        100.0 * within_norm / result.real_incidents, 1
    ) if result.real_incidents else 100.0
    result.correct_pct = round(
        100.0 * result.correct_incidents / result.total_incidents, 1
    ) if result.total_incidents else 0.0
    result.accuracy_pct = result.correct_pct

    # Aggregate score (0..100): correctness + norm compliance minus penalties.
    penalty_pool = max(
        0.0,
        100.0
        - result.error_count * 10.0
        - max(0, result.decision_changes - scenario.criteria.max_decision_changes)
        * 5.0,
    )
    score = (
        0.5 * result.correct_pct
        + 0.3 * result.norm_compliance_pct
        + 0.2 * penalty_pool
    )
    result.score = round(max(0.0, min(100.0, score)), 1)
    result.passed = (
        result.score >= scenario.criteria.pass_score
        and result.error_count <= scenario.criteria.max_errors
    )
    return result
