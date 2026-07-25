"""Dispatch recommendation REST endpoints.

    POST /dispatch/recommend      — full recommended composition (advisory)
    POST /dispatch/preview        — quick preview (top candidates, no reserves)
    GET  /dispatch/rules          — the configured incident rules
    GET  /dispatch/capabilities   — the capability catalog

The system only *recommends*; it never dispatches units.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.dispatch.deps import DispatchServiceDep
from app.dispatch.schemas.requests import DispatchRequest
from app.dispatch.schemas.responses import (
    CapabilityInfo,
    DispatchResponse,
    RuleResponse,
)

router = APIRouter(prefix="/dispatch", tags=["dispatch"])


@router.post(
    "/recommend",
    response_model=DispatchResponse,
    summary="Recommend forces & equipment for an incident",
)
async def recommend(
    service: DispatchServiceDep, request: DispatchRequest
) -> DispatchResponse:
    return await service.recommend(request, preview=False)


@router.post(
    "/preview",
    response_model=DispatchResponse,
    summary="Preview candidates without a full composition",
)
async def preview(
    service: DispatchServiceDep, request: DispatchRequest
) -> DispatchResponse:
    return await service.recommend(request, preview=True)


@router.get("/rules", response_model=list[RuleResponse], summary="List incident rules")
async def rules(service: DispatchServiceDep) -> list[RuleResponse]:
    return await service.list_rules()


@router.get(
    "/capabilities",
    response_model=list[CapabilityInfo],
    summary="List available capabilities",
)
async def capabilities(service: DispatchServiceDep) -> list[CapabilityInfo]:
    return await service.list_capabilities()
