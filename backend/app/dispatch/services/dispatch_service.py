"""DispatchService — API-facing orchestration.

Resolves the incident location (coordinates or geocoded address via GIS), runs
the DispatchEngine, and maps the domain recommendation to API schemas. Also
exposes the rule and capability catalogs. Advisory only — nothing is dispatched.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.dispatch.algorithms.scoring import ArrivalEstimator
from app.dispatch.engine import DispatchEngine
from app.dispatch.repositories import CandidateRepository
from app.dispatch.rules import RuleEngine
from app.dispatch.schemas.requests import DispatchRequest
from app.dispatch.schemas.responses import (
    CapabilityInfo,
    DispatchResponse,
    RuleResponse,
)
from app.dispatch.utils.mapping import rule_to_response, to_dispatch_response
from app.gis.services.geocoding import GeocodingService
from app.models.catalog import Capability


class DispatchService:
    """Produces dispatch recommendations for the dispatcher."""

    def __init__(
        self,
        session: AsyncSession,
        rule_engine: RuleEngine,
        *,
        geocoding: GeocodingService | None = None,
        arrival_estimator: ArrivalEstimator | None = None,
    ) -> None:
        self._session = session
        self._rules = rule_engine
        self._geocoding = geocoding
        self._engine = DispatchEngine(
            CandidateRepository(session),
            rule_engine,
            arrival_estimator=arrival_estimator,
        )

    async def recommend(
        self, request: DispatchRequest, *, preview: bool = False
    ) -> DispatchResponse:
        if not self._rules.has_incident_type(request.incident_type):
            raise ValidationError(f"Unknown incident type: {request.incident_type!r}")
        latitude, longitude = await self._resolve_point(request)
        recommendation = await self._engine.recommend(
            incident_type=request.incident_type,
            latitude=latitude,
            longitude=longitude,
            preview=preview,
        )
        return to_dispatch_response(recommendation)

    async def list_rules(self) -> list[RuleResponse]:
        return [rule_to_response(rule) for rule in self._rules.incident_types()]

    async def list_capabilities(self) -> list[CapabilityInfo]:
        rows = await self._session.execute(
            select(Capability).where(Capability.is_deleted.is_(False))
        )
        return [
            CapabilityInfo(
                id=c.id, code=c.code, name=c.name, description=c.description
            )
            for c in rows.scalars().all()
        ]

    async def _resolve_point(self, request: DispatchRequest) -> tuple[float, float]:
        if request.latitude is not None and request.longitude is not None:
            return request.latitude, request.longitude
        if request.address and self._geocoding is not None:
            outcome = await self._geocoding.geocode(request.address, limit=1)
            if outcome.results:
                best = outcome.results[0]
                return best.latitude, best.longitude
            raise ValidationError("Address could not be geocoded")
        raise ValidationError("Provide latitude/longitude or a geocodable address")
