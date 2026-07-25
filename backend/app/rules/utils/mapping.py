"""Mapping between ORM rules and API schemas."""

from __future__ import annotations

from collections import defaultdict

from app.models.enums import ResourceCategory
from app.rules.models.entities import Rule, RuleVersion
from app.rules.repositories import active_version
from app.rules.schemas.content import (
    ActionResponse,
    CapabilityRequirementResponse,
    ConditionResponse,
    ResourceRequirementResponse,
)
from app.rules.schemas.rule import (
    RuleResponse,
    RuleSummaryResponse,
    RuleVersionResponse,
    RuleVersionSummary,
)
from app.rules.schemas.service import CompositionItem, RequirementsResponse


def version_to_response(version: RuleVersion) -> RuleVersionResponse:
    return RuleVersionResponse(
        id=version.id,
        created_at=version.created_at,
        updated_at=version.updated_at,
        is_deleted=version.is_deleted,
        rule_id=version.rule_id,
        version_number=version.version_number,
        status=version.status,
        priority=version.priority,
        is_active=version.is_active,
        effective_from=version.effective_from,
        effective_to=version.effective_to,
        notes=version.notes,
        published_at=version.published_at,
        conditions=[
            ConditionResponse(
                id=c.id, condition_type=c.condition_type, operator=c.operator,
                field=c.field, value=c.value,
            )
            for c in version.conditions
            if not c.is_deleted
        ],
        actions=[
            ActionResponse(
                id=a.id, action_type=a.action_type, parameters=a.parameters,
                sort_order=a.sort_order,
            )
            for a in version.actions
            if not a.is_deleted
        ],
        resource_requirements=[
            _resource_req(r) for r in version.resource_requirements if not r.is_deleted
        ],
        capability_requirements=[
            CapabilityRequirementResponse(
                id=c.id, capability_code=c.capability_code,
                min_quantity=c.min_quantity, mandatory=c.mandatory,
            )
            for c in version.capability_requirements
            if not c.is_deleted
        ],
    )


def _resource_req(r) -> ResourceRequirementResponse:
    return ResourceRequirementResponse(
        id=r.id,
        resource_category=r.resource_category,
        vehicle_type_code=r.vehicle_type_code,
        min_count=r.min_count,
        recommended_count=r.recommended_count,
        reserve_count=r.reserve_count,
        priority=r.priority,
        notes=r.notes,
    )


def rule_to_response(rule: Rule) -> RuleResponse:
    version = active_version(rule)
    return RuleResponse(
        id=rule.id,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
        is_deleted=rule.is_deleted,
        code=rule.code,
        name=rule.name,
        description=rule.description,
        is_enabled=rule.is_enabled,
        category_id=rule.category_id,
        rule_set_id=rule.rule_set_id,
        tags=sorted(t.tag for t in rule.tags if not t.is_deleted),
        incident_type_ids=[
            i.incident_type_id for i in rule.incident_types if not i.is_deleted
        ],
        complexities=[
            c.complexity for c in rule.incident_categories if not c.is_deleted
        ],
        active_version=version_to_response(version) if version else None,
    )


def rule_to_summary(rule: Rule) -> RuleSummaryResponse:
    version = active_version(rule)
    return RuleSummaryResponse(
        id=rule.id,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
        is_deleted=rule.is_deleted,
        code=rule.code,
        name=rule.name,
        is_enabled=rule.is_enabled,
        category_id=rule.category_id,
        active_version=(
            RuleVersionSummary(
                id=version.id,
                created_at=version.created_at,
                updated_at=version.updated_at,
                is_deleted=version.is_deleted,
                rule_id=version.rule_id,
                version_number=version.version_number,
                status=version.status,
                priority=version.priority,
                is_active=version.is_active,
                published_at=version.published_at,
            )
            if version
            else None
        ),
    )


def to_requirements(rule: Rule, version: RuleVersion) -> RequirementsResponse:
    minimum: dict[ResourceCategory, int] = defaultdict(int)
    recommended: dict[ResourceCategory, int] = defaultdict(int)
    reserve: dict[ResourceCategory, int] = defaultdict(int)
    for r in version.resource_requirements:
        if r.is_deleted:
            continue
        minimum[r.resource_category] += r.min_count
        recommended[r.resource_category] += r.recommended_count
        reserve[r.resource_category] += r.reserve_count

    return RequirementsResponse(
        rule_id=rule.id,
        rule_code=rule.code,
        version_number=version.version_number,
        resource_requirements=[
            _resource_req(r) for r in version.resource_requirements if not r.is_deleted
        ],
        capability_requirements=[
            CapabilityRequirementResponse(
                id=c.id, capability_code=c.capability_code,
                min_quantity=c.min_quantity, mandatory=c.mandatory,
            )
            for c in version.capability_requirements
            if not c.is_deleted
        ],
        minimum_composition=[
            CompositionItem(resource_category=k, count=v) for k, v in minimum.items()
        ],
        recommended_composition=[
            CompositionItem(resource_category=k, count=v)
            for k, v in recommended.items()
        ],
        reserve_composition=[
            CompositionItem(resource_category=k, count=v) for k, v in reserve.items()
        ],
        required_capabilities=sorted(
            c.capability_code
            for c in version.capability_requirements
            if c.mandatory and not c.is_deleted
        ),
    )
