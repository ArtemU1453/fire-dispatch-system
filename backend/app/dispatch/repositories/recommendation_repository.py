"""Persistence for dispatch recommendations (write, read-one, history).

Loads the full aggregate eagerly (items + their resources and reasons, coverage,
resource-match log, summary and decision) so mapping to schemas never triggers a
lazy load under the async engine.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dispatch.models.entities import (
    Recommendation,
    RecommendationItem,
    ResourceMatch,
)
from app.models.resource import Resource, ResourceCapability


def _full_load_options() -> list:
    item_resource = selectinload(Recommendation.items).selectinload(
        RecommendationItem.resource
    )
    return [
        selectinload(Recommendation.items).selectinload(RecommendationItem.reasons),
        item_resource.selectinload(Resource.resource_type),
        item_resource.selectinload(Resource.organization),
        item_resource.selectinload(Resource.availability_status),
        item_resource.selectinload(Resource.capability_links).selectinload(
            ResourceCapability.capability
        ),
        selectinload(Recommendation.reasons),
        selectinload(Recommendation.capability_matches),
        selectinload(Recommendation.resource_matches).selectinload(
            ResourceMatch.resource
        ),
        selectinload(Recommendation.summary),
        selectinload(Recommendation.decision),
    ]


class RecommendationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, recommendation: Recommendation) -> Recommendation:
        self._session.add(recommendation)
        await self._session.flush()
        return await self.get_full(recommendation.id)

    async def get_full(self, recommendation_id: UUID) -> Recommendation | None:
        stmt = (
            select(Recommendation)
            .where(
                Recommendation.id == recommendation_id,
                Recommendation.is_deleted.is_(False),
            )
            .options(*_full_load_options())
        )
        return (await self._session.execute(stmt)).scalars().first()

    async def latest_for_incident(
        self, incident_id: UUID, *, include_preview: bool = False
    ) -> Recommendation | None:
        stmt = select(Recommendation).where(
            Recommendation.incident_id == incident_id,
            Recommendation.is_deleted.is_(False),
        )
        if not include_preview:
            stmt = stmt.where(Recommendation.is_preview.is_(False))
        stmt = (
            stmt.order_by(Recommendation.created_at.desc())
            .limit(1)
            .options(*_full_load_options())
        )
        return (await self._session.execute(stmt)).scalars().first()

    async def history_for_incident(
        self, incident_id: UUID, *, limit: int = 50, offset: int = 0
    ) -> Sequence[Recommendation]:
        stmt = (
            select(Recommendation)
            .where(
                Recommendation.incident_id == incident_id,
                Recommendation.is_deleted.is_(False),
            )
            .order_by(Recommendation.created_at.desc())
            .limit(limit)
            .offset(offset)
            .options(selectinload(Recommendation.items))
        )
        return (await self._session.execute(stmt)).scalars().all()
