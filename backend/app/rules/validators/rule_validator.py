"""Rule validation — well-formedness checks before publishing.

A draft may be incomplete, but a version must be valid before it is published
(and thereby made immutable / activatable). The validator returns a list of
human-readable problems; an empty list means the version is publishable.
"""

from __future__ import annotations

from app.rules.models import ConditionOperator
from app.rules.models.entities import RuleCondition, RuleVersion

# Operators that require a scalar ``value``.
_SCALAR_OPS = {
    ConditionOperator.EQ,
    ConditionOperator.NEQ,
    ConditionOperator.GTE,
    ConditionOperator.LTE,
    ConditionOperator.CONTAINS,
}
# Operators that require a ``values`` list.
_LIST_OPS = {ConditionOperator.IN, ConditionOperator.NOT_IN}


class RuleValidator:
    """Validates a rule version for publishing."""

    def validate_for_publish(self, version: RuleVersion) -> list[str]:
        errors: list[str] = []
        if not (
            version.resource_requirements
            or version.capability_requirements
            or version.actions
        ):
            errors.append(
                "A rule version must define at least one requirement or action."
            )
        for condition in version.conditions:
            errors.extend(self._validate_condition(condition))

        codes = [c.capability_code for c in version.capability_requirements]
        if len(codes) != len(set(codes)):
            errors.append("Duplicate capability requirement codes.")

        for req in version.resource_requirements:
            if req.min_count > req.recommended_count and req.recommended_count > 0:
                errors.append(
                    f"Resource requirement for {req.resource_category.value}: "
                    "min_count exceeds recommended_count."
                )
        return errors

    @staticmethod
    def _validate_condition(condition: RuleCondition) -> list[str]:
        errors: list[str] = []
        payload = condition.value or {}
        op = condition.operator
        label = condition.condition_type.value
        if op in _SCALAR_OPS and "value" not in payload:
            errors.append(f"Condition '{label}' ({op.value}) requires a 'value'.")
        if op in _LIST_OPS and not payload.get("values"):
            errors.append(f"Condition '{label}' ({op.value}) requires 'values'.")
        if op is ConditionOperator.BETWEEN and (
            "min" not in payload or "max" not in payload
        ):
            errors.append(f"Condition '{label}' (between) requires 'min' and 'max'.")
        return errors
