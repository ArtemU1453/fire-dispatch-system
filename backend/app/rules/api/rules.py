"""Rules REST endpoints.

    GET    /rules                     — list rules (summaries)
    GET    /rules/{id}                — one rule (with active version)
    GET    /rules/incident/{type}     — active rules for an incident type
    GET    /rules/category/{category} — rules in a category
    GET    /rules/versions/{id}       — all versions of a rule
    GET    /rules/{id}/requirements   — ready-made requirements (active version)
    POST   /rules                     — create a rule (+ first version)
    PUT    /rules/{id}                — update metadata / add a version
    DELETE /rules/{id}                — soft-delete a rule
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from app.rules.deps import RuleServiceDep
from app.rules.schemas.rule import (
    RuleCreate,
    RuleResponse,
    RuleSummaryResponse,
    RuleUpdate,
    RuleVersionResponse,
)
from app.rules.schemas.service import RequirementsResponse

router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("", response_model=list[RuleSummaryResponse], summary="List rules")
async def list_rules(
    service: RuleServiceDep,
    category_id: UUID | None = Query(default=None),
    enabled_only: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[RuleSummaryResponse]:
    return await service.list_rules(
        category_id=category_id, enabled_only=enabled_only, limit=limit, offset=offset
    )


@router.post(
    "", response_model=RuleResponse, status_code=status.HTTP_201_CREATED,
    summary="Create a rule",
)
async def create_rule(service: RuleServiceDep, data: RuleCreate) -> RuleResponse:
    return await service.create_rule(data)


@router.get(
    "/incident/{incident_type_id}",
    response_model=list[RuleResponse],
    summary="Active rules for an incident type",
)
async def rules_for_incident(
    service: RuleServiceDep, incident_type_id: UUID
) -> list[RuleResponse]:
    return await service.get_by_incident_type(incident_type_id)


@router.get(
    "/category/{category_id}",
    response_model=list[RuleSummaryResponse],
    summary="Rules in a category",
)
async def rules_for_category(
    service: RuleServiceDep, category_id: UUID
) -> list[RuleSummaryResponse]:
    return await service.get_by_category(category_id)


@router.get(
    "/versions/{rule_id}",
    response_model=list[RuleVersionResponse],
    summary="All versions of a rule",
)
async def rule_versions(
    service: RuleServiceDep, rule_id: UUID
) -> list[RuleVersionResponse]:
    return await service.get_versions(rule_id)


@router.get(
    "/{rule_id}/requirements",
    response_model=RequirementsResponse,
    summary="Ready-made requirements from the active version",
)
async def rule_requirements(
    service: RuleServiceDep, rule_id: UUID
) -> RequirementsResponse:
    return await service.get_requirements(rule_id)


@router.get("/{rule_id}", response_model=RuleResponse, summary="Get a rule")
async def get_rule(service: RuleServiceDep, rule_id: UUID) -> RuleResponse:
    return await service.get_rule(rule_id)


@router.put("/{rule_id}", response_model=RuleResponse, summary="Update a rule")
async def update_rule(
    service: RuleServiceDep, rule_id: UUID, data: RuleUpdate
) -> RuleResponse:
    return await service.update_rule(rule_id, data)


@router.delete(
    "/{rule_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a rule"
)
async def delete_rule(service: RuleServiceDep, rule_id: UUID) -> Response:
    await service.delete_rule(rule_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
