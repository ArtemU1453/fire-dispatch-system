"""Condition evaluation — the applicability engine.

Given an :class:`EvaluationContext` (the incident's facts) a rule version is
*applicable* when **all** its conditions pass (logical AND). A version with no
conditions is unconditionally applicable. The Rule Engine performs no dispatch —
it only decides which rules apply and returns them.

Condition values are stored as JSONB with a small convention:
``{"value": x}`` (scalar), ``{"values": [...]}`` (list), ``{"min": a, "max": b}``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from app.rules.models import ConditionOperator, ConditionType
from app.rules.models.entities import RuleCondition, RuleVersion


@dataclass(slots=True)
class EvaluationContext:
    """The facts about an incident used to evaluate rule conditions."""

    incident_type_id: UUID | None = None
    incident_type_code: str | None = None
    complexity: str | None = None
    time_of_day_hour: int | None = None
    administrative_area_id: UUID | None = None
    object_type: str | None = None
    priority: str | None = None
    available_resource_count: int | None = None
    available_capabilities: set[str] = field(default_factory=set)

    def value_for(self, condition_type: ConditionType) -> Any:
        return {
            ConditionType.INCIDENT_TYPE: (
                self.incident_type_code
                if self.incident_type_code is not None
                else (str(self.incident_type_id) if self.incident_type_id else None)
            ),
            ConditionType.INCIDENT_COMPLEXITY: self.complexity,
            ConditionType.TIME_OF_DAY: self.time_of_day_hour,
            ConditionType.ADMINISTRATIVE_AREA: (
                str(self.administrative_area_id)
                if self.administrative_area_id
                else None
            ),
            ConditionType.OBJECT_TYPE: self.object_type,
            ConditionType.PRIORITY: self.priority,
            ConditionType.RESOURCE_AVAILABILITY: self.available_resource_count,
            ConditionType.CAPABILITY: self.available_capabilities,
        }.get(condition_type)


class ConditionExecutor:
    """Evaluates a single :class:`RuleCondition` against a context."""

    def evaluate(self, condition: RuleCondition, context: EvaluationContext) -> bool:
        actual = context.value_for(condition.condition_type)
        payload = condition.value or {}
        op = condition.operator

        if op is ConditionOperator.EXISTS:
            return actual is not None and actual != [] and actual != set()

        if actual is None:
            # No fact to compare against → the condition cannot be satisfied,
            # except EXISTS handled above.
            return False

        scalar = payload.get("value")
        values = payload.get("values", [])

        if op is ConditionOperator.EQ:
            return _as_str(actual) == _as_str(scalar)
        if op is ConditionOperator.NEQ:
            return _as_str(actual) != _as_str(scalar)
        if op is ConditionOperator.IN:
            return _as_str(actual) in {_as_str(v) for v in values}
        if op is ConditionOperator.NOT_IN:
            return _as_str(actual) not in {_as_str(v) for v in values}
        if op is ConditionOperator.GTE:
            return _num(actual) >= _num(scalar)
        if op is ConditionOperator.LTE:
            return _num(actual) <= _num(scalar)
        if op is ConditionOperator.BETWEEN:
            return _num(payload.get("min")) <= _num(actual) <= _num(payload.get("max"))
        if op is ConditionOperator.CONTAINS:
            collection = actual if isinstance(actual, (set, list, tuple)) else {actual}
            return _as_str(scalar) in {_as_str(v) for v in collection}
        return False


class RuleEvaluator:
    """Evaluates all conditions of a rule version (logical AND)."""

    def __init__(self, executor: ConditionExecutor | None = None) -> None:
        self._executor = executor or ConditionExecutor()

    def is_applicable(
        self, version: RuleVersion, context: EvaluationContext
    ) -> bool:
        return all(
            self._executor.evaluate(condition, context)
            for condition in self._active_conditions(version)
        )

    @staticmethod
    def _active_conditions(version: RuleVersion) -> Sequence[RuleCondition]:
        return [c for c in version.conditions if not c.is_deleted]


def _as_str(value: Any) -> str:
    return "" if value is None else str(value)


def _num(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")
