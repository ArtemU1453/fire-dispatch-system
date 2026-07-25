"""Dispatch recommendation REST endpoints.

    POST /dispatch/recommend             — full recommended composition (advisory)
    POST /dispatch/preview               — quick preview (top candidates, no reserve)
    GET  /dispatch/{incident_id}         — latest recommendation for an incident
    GET  /dispatch/history/{incident_id} — recommendation history for an incident

The system only *recommends*; it never dispatches units.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query

from app.dispatch.deps import DispatchServiceDep
from app.dispatch.schemas.requests import DispatchRequest
from app.dispatch.schemas.responses import (
    DispatchResponse,
    RecommendationHistoryItem,
    RecommendationResponse,
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
    summary="Preview a composition without reserves",
)
async def preview(
    service: DispatchServiceDep, request: DispatchRequest
) -> DispatchResponse:
    return await service.recommend(request, preview=True)


@router.get(
    "/history/{incident_id}",
    response_model=list[RecommendationHistoryItem],
    summary="Recommendation history for an incident",
)
async def history(
    service: DispatchServiceDep,
    incident_id: UUID,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[RecommendationHistoryItem]:
    return await service.get_history(incident_id, limit=limit, offset=offset)


@router.get(
    "/{incident_id}",
    response_model=RecommendationResponse,
    summary="Latest recommendation for an incident",
)
async def get_recommendation(
    service: DispatchServiceDep, incident_id: UUID
) -> RecommendationResponse:
    return await service.get_recommendation(incident_id)
