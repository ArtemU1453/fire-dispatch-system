"""DispatchService — API-facing orchestration.

Validates the request, resolves the incident location (coordinates or geocoded
address via GIS), runs the :class:`DispatchEngine`, persists the recommendation
(with its full explanation and log) and maps it to API schemas. Also serves the
recommendation retrieval and history endpoints. Advisory only — nothing is
dispatched.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.dispatch.config import DispatchConfig
from app.dispatch.engine import DispatchEngine, IncidentContext
from app.dispatch.eta import ETAProvider
from app.dispatch.repositories import CandidateRepository, RecommendationRepository
from app.dispatch.requirements import RequirementSet
from app.dispatch.schemas.requests import DispatchRequest
from app.dispatch.schemas.responses import (
    CapabilityResponse,
    DispatchResponse,
    RecommendationHistoryItem,
    RecommendationResponse,
)
from app.dispatch.utils.mapping import (
    outcome_to_orm,
    recommendation_to_history_item,
    recommendation_to_response,
)
from app.dispatch.validators import DispatchValidator
from app.gis.services.geocoding import GeocodingService
from app.models.catalog import Capability, IncidentType
from app.rules.engine import RuleEngine
from app.rules.repositories import RuleRepository


class DispatchService:
    """Produces, stores and serves dispatch recommendations."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        geocoding: GeocodingService | None = None,
        config: DispatchConfig | None = None,
        eta_provider: ETAProvider | None = None,
    ) -> None:
        self._session = session
        self._geocoding = geocoding
        self._config = config or DispatchConfig()
        self._validator = DispatchValidator()
        self._recommendations = RecommendationRepository(session)
        self._engine = DispatchEngine(
            RuleEngine(RuleRepository(session)),
            CandidateRepository(session),
            config=self._config,
            eta_provider=eta_provider,
        )

    async def recommend(
        self, request: DispatchRequest, *, preview: bool = False
    ) -> DispatchResponse:
        self._validator.validate(request)
        await self._ensure_incident_type(request.incident_type_id)
        latitude, longitude = await self._resolve_point(request)

        incident = IncidentContext(
            incident_type_id=request.incident_type_id,
            latitude=latitude,
            longitude=longitude,
            complexity=(
                request.complexity.value if request.complexity is not None else None
            ),
            time_of_day_hour=request.constraints.time_of_day_hour,
            administrative_area_id=request.administrative_area_id,
            object_type=request.object_type,
            danger_level=request.danger_level,
            flags=list(request.flags),
            organization_ids=list(request.constraints.organization_ids),
            excluded_resource_ids=set(request.constraints.excluded_resource_ids),
            radius_override_meters=request.constraints.radius_meters,
        )

        outcome = await self._engine.recommend(incident, preview=preview)

        orm = outcome_to_orm(
            outcome,
            incident_id=request.incident_id,
            complexity=request.complexity,
            address=request.address,
            administrative_area_id=request.administrative_area_id,
            danger_level=request.danger_level,
            request_snapshot=request.model_dump(mode="json"),
        )
        stored = await self._recommendations.add(orm)
        required = await self._required_capabilities(outcome.requirements)
        return DispatchResponse(
            recommendation=recommendation_to_response(
                stored, required_capabilities=required
            )
        )

    async def get_recommendation(self, incident_id: UUID) -> RecommendationResponse:
        """Latest (non-preview) recommendation for an incident."""
        rec = await self._recommendations.latest_for_incident(incident_id)
        if rec is None:
            raise NotFoundError("No recommendation found for this incident")
        return recommendation_to_response(rec)

    async def get_history(
        self, incident_id: UUID, *, limit: int = 50, offset: int = 0
    ) -> list[RecommendationHistoryItem]:
        rows = await self._recommendations.history_for_incident(
            incident_id, limit=limit, offset=offset
        )
        return [recommendation_to_history_item(r) for r in rows]

    # ---------------------------------------------------------- internals
    async def _ensure_incident_type(self, incident_type_id: UUID) -> None:
        row = await self._session.execute(
            select(IncidentType.id).where(
                IncidentType.id == incident_type_id,
                IncidentType.is_deleted.is_(False),
            )
        )
        if row.first() is None:
            raise ValidationError(f"Unknown incident type: {incident_type_id}")

    async def _required_capabilities(
        self, requirements: RequirementSet
    ) -> list[CapabilityResponse]:
        codes = requirements.required_capability_codes
        labels: dict[str, str] = {}
        if codes:
            rows = await self._session.execute(
                select(Capability.code, Capability.name).where(
                    Capability.code.in_(codes)
                )
            )
            labels = {code: name for code, name in rows.all()}
        return [
            CapabilityResponse(
                code=need.code,
                min_quantity=need.min_quantity,
                mandatory=need.mandatory,
                label=labels.get(need.code),
            )
            for need in sorted(
                requirements.capabilities.values(), key=lambda n: n.code
            )
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
