"""Schemas for rules, versions, categories and rule sets."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.rules.models.enums import (
    IncidentComplexity,
    RulePriority,
    RuleStatus,
)
from app.rules.schemas.content import (
    ActionResponse,
    CapabilityRequirementResponse,
    ConditionResponse,
    ResourceRequirementResponse,
    VersionContentInput,
)
from app.schemas.common import ResponseBase, SchemaBase


# --------------------------------------------------------------- category ----
class RuleCategoryCreate(SchemaBase):
    code: str
    name: str
    description: str | None = None


class RuleCategoryUpdate(SchemaBase):
    code: str | None = None
    name: str | None = None
    description: str | None = None


class RuleCategoryResponse(ResponseBase):
    code: str
    name: str
    description: str | None = None


# --------------------------------------------------------------- rule set ----
class RuleSetCreate(SchemaBase):
    code: str
    name: str
    description: str | None = None


class RuleSetUpdate(SchemaBase):
    code: str | None = None
    name: str | None = None
    description: str | None = None


class RuleSetResponse(ResponseBase):
    code: str
    name: str
    description: str | None = None


# ----------------------------------------------------------------- version ---
class RuleVersionResponse(ResponseBase):
    rule_id: UUID
    version_number: int
    status: RuleStatus
    priority: RulePriority
    is_active: bool
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    notes: str | None = None
    published_at: datetime | None = None
    conditions: list[ConditionResponse] = []
    actions: list[ActionResponse] = []
    resource_requirements: list[ResourceRequirementResponse] = []
    capability_requirements: list[CapabilityRequirementResponse] = []


class RuleVersionSummary(ResponseBase):
    rule_id: UUID
    version_number: int
    status: RuleStatus
    priority: RulePriority
    is_active: bool
    published_at: datetime | None = None


# -------------------------------------------------------------------- rule ---
class RuleCreate(SchemaBase):
    code: str
    name: str
    description: str | None = None
    category_id: UUID
    rule_set_id: UUID | None = None
    is_enabled: bool = True
    incident_type_ids: list[UUID] = []
    complexities: list[IncidentComplexity] = []
    tags: list[str] = []
    version: VersionContentInput
    publish: bool = False


class RuleUpdate(SchemaBase):
    name: str | None = None
    description: str | None = None
    is_enabled: bool | None = None
    rule_set_id: UUID | None = None
    incident_type_ids: list[UUID] | None = None
    complexities: list[IncidentComplexity] | None = None
    tags: list[str] | None = None
    # Providing a new version creates it (published rules are immutable).
    new_version: VersionContentInput | None = None
    publish: bool = False


class RuleResponse(ResponseBase):
    code: str
    name: str
    description: str | None = None
    is_enabled: bool
    category_id: UUID
    rule_set_id: UUID | None = None
    tags: list[str] = []
    incident_type_ids: list[UUID] = []
    complexities: list[IncidentComplexity] = []
    active_version: RuleVersionResponse | None = None


class RuleSummaryResponse(ResponseBase):
    code: str
    name: str
    is_enabled: bool
    category_id: UUID
    active_version: RuleVersionSummary | None = None
