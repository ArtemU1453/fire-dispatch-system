"""Shared PostgreSQL enum type objects.

Reusing one ``ENUM`` object per type name (rather than an inline ``Enum`` per
column) ensures each native enum is declared once, even when used on several
columns.

- New rules enums use ``values_callable`` so the DB labels are the enum *values*
  (lowercase), matching the ``server_default``s and the value-based Pydantic
  serialization used across the project.
- ``create_type=False`` on every object: the enum types are created/dropped
  explicitly and exactly once in the migration (see the rules migration), which
  avoids duplicate ``CREATE TYPE`` when a type is used by several tables and
  avoids re-creating ``resource_category`` (already created in Stage 2).
"""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy.dialects.postgresql import ENUM

from app.models.enums import ResourceCategory
from app.rules.models.enums import (
    ActionType,
    ConditionOperator,
    ConditionType,
    IncidentComplexity,
    RuleHistoryAction,
    RulePriority,
    RuleStatus,
)


def _values(enum_cls: Iterable) -> list[str]:
    return [member.value for member in enum_cls]


def _enum(py_enum, name: str) -> ENUM:
    return ENUM(
        py_enum,
        name=name,
        create_type=False,
        values_callable=_values,
    )


rule_status_enum = _enum(RuleStatus, "rule_status")
rule_priority_enum = _enum(RulePriority, "rule_priority")
incident_complexity_enum = _enum(IncidentComplexity, "incident_complexity")
condition_type_enum = _enum(ConditionType, "rule_condition_type")
condition_operator_enum = _enum(ConditionOperator, "rule_condition_operator")
action_type_enum = _enum(ActionType, "rule_action_type")
history_action_enum = _enum(RuleHistoryAction, "rule_history_action")

# All new enum types managed explicitly by the migration.
NEW_ENUMS = (
    rule_status_enum,
    rule_priority_enum,
    incident_complexity_enum,
    condition_type_enum,
    condition_operator_enum,
    action_type_enum,
    history_action_enum,
)

# Already exists (Stage 2) — never (re)created here; labels are the enum NAMES.
resource_category_enum = ENUM(
    ResourceCategory, name="resource_category", create_type=False
)
