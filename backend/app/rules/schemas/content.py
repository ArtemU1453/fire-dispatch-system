"""Schemas for a rule version's content (conditions, actions, requirements).

These nested items are created / replaced as part of a version (versions are
immutable once published), so they expose an ``Input`` (create) and a
``Response`` shape rather than an independent update.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from app.models.enums import ResourceCategory
from app.rules.models.enums import (
    ActionType,
    ConditionOperator,
    ConditionType,
    RulePriority,
)
from app.schemas.common import SchemaBase


# ------------------------------------------------------------------ inputs ---
class ConditionInput(SchemaBase):
    condition_type: ConditionType
    operator: ConditionOperator
    field: str | None = None
    value: dict[str, Any] | None = None


class ActionInput(SchemaBase):
    action_type: ActionType
    parameters: dict[str, Any] | None = None
    sort_order: int = 0


class ResourceRequirementInput(SchemaBase):
    resource_category: ResourceCategory
    vehicle_type_code: str | None = None
    min_count: int = 0
    recommended_count: int = 0
    reserve_count: int = 0
    priority: RulePriority = RulePriority.NORMAL
    notes: str | None = None


class CapabilityRequirementInput(SchemaBase):
    capability_code: str
    min_quantity: int = 1
    mandatory: bool = True


class VersionContentInput(SchemaBase):
    """The content of a new rule version."""

    priority: RulePriority = RulePriority.NORMAL
    notes: str | None = None
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    conditions: list[ConditionInput] = []
    actions: list[ActionInput] = []
    resource_requirements: list[ResourceRequirementInput] = []
    capability_requirements: list[CapabilityRequirementInput] = []


# --------------------------------------------------------------- responses ---
class ConditionResponse(SchemaBase):
    id: UUID
    condition_type: ConditionType
    operator: ConditionOperator
    field: str | None = None
    value: dict[str, Any] | None = None


class ActionResponse(SchemaBase):
    id: UUID
    action_type: ActionType
    parameters: dict[str, Any] | None = None
    sort_order: int


class ResourceRequirementResponse(SchemaBase):
    id: UUID
    resource_category: ResourceCategory
    vehicle_type_code: str | None = None
    min_count: int
    recommended_count: int
    reserve_count: int
    priority: RulePriority
    notes: str | None = None


class CapabilityRequirementResponse(SchemaBase):
    id: UUID
    capability_code: str
    min_quantity: int
    mandatory: bool
