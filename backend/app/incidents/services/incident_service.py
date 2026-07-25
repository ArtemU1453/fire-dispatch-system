"""IncidentService — the heart of incident management.

Creates and edits incidents, drives the lifecycle **state machine**, records the
**timeline**, the field-level **history** and the technical **log**, links
**recommendations** (Dispatch Engine) and **dispatched units** (resources), and
closes / archives incidents. Every change to the card is recorded (who, when,
old → new, source).

Only existing services and models are reused; nothing from earlier stages is
modified.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.incidents.attachments import AttachmentService
from app.incidents.history import HistoryRecorder
from app.incidents.models.entities import (
    Incident,
    IncidentComment,
    IncidentDispatch,
    IncidentLocation,
    IncidentRecommendation,
)
from app.incidents.models.enums import (
    IncidentStatus,
    TimelineEventType,
)
from app.incidents.repositories import IncidentRepository
from app.incidents.schemas.incident import (
    AssignUnitsRequest,
    CommentCreate,
    IncidentCreate,
    IncidentUpdate,
    StatusChangeRequest,
)
from app.incidents.timeline import TimelineRecorder
from app.incidents.utils.actor import Actor
from app.incidents.utils.log_recorder import IncidentLogger
from app.incidents.validators.state_machine import (
    InvalidTransitionError,
    can_transition,
)

# Fields whose change is recorded in the audit history.
_TRACKED_FIELDS = (
    "incident_type_id",
    "category",
    "source",
    "priority",
    "title",
    "description",
    "address",
    "latitude",
    "longitude",
    "administrative_area_id",
    "danger_level",
    "object_type",
    "reporter_name",
    "reporter_contact",
)


def _now() -> datetime:
    return datetime.now(tz=UTC)


class IncidentService:
    """Application service for the incident lifecycle."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = IncidentRepository(session)
        self._timeline = TimelineRecorder()
        self._history = HistoryRecorder()
        self._log = IncidentLogger()
        self._attachments = AttachmentService(self._timeline)

    # ------------------------------------------------------------- reads
    async def get(self, incident_id: UUID) -> Incident:
        incident = await self._repo.get_full(incident_id)
        if incident is None:
            raise NotFoundError("Incident not found")
        return incident

    async def list_incidents(
        self, *, active: bool | None = None, limit: int = 100, offset: int = 0
    ) -> Sequence[Incident]:
        return await self._repo.list_incidents(
            active=active, limit=limit, offset=offset
        )

    # ------------------------------------------------------------- create
    async def create(self, data: IncidentCreate) -> Incident:
        number = data.number or await self._repo.next_number()
        if await self._repo.get_by_number(number) is not None:
            raise ConflictError(f"Incident number already exists: {number}")
        actor = Actor(name=data.actor_name)

        incident = Incident(
            number=number,
            incident_type_id=data.incident_type_id,
            category=data.category,
            source=data.source,
            status=IncidentStatus.CREATED,
            priority=data.priority,
            title=data.title,
            description=data.description,
            address=data.address,
            latitude=data.latitude,
            longitude=data.longitude,
            administrative_area_id=data.administrative_area_id,
            danger_level=data.danger_level,
            object_type=data.object_type,
            reporter_name=data.reporter_name,
            reporter_contact=data.reporter_contact,
            reported_at=_now(),
            created_by_user_id=actor.user_id,
        )
        if data.address or (data.latitude is not None and data.longitude is not None):
            incident.locations.append(
                IncidentLocation(
                    address=data.address,
                    latitude=data.latitude,
                    longitude=data.longitude,
                    administrative_area_id=data.administrative_area_id,
                    is_primary=True,
                    source="manual",
                )
            )
        self._timeline.record(
            incident,
            TimelineEventType.CREATED,
            f"Создана карточка происшествия {number}",
            actor=actor,
        )
        self._log.log(incident, "created", message=number, actor=actor)

        self._session.add(incident)
        await self._session.flush()
        return await self._require(incident.id)

    # ------------------------------------------------------------- update
    async def update(self, incident_id: UUID, data: IncidentUpdate) -> Incident:
        incident = await self.get(incident_id)
        actor = Actor(name=data.actor_name)
        changes: dict[str, tuple] = {}

        payload = data.model_dump(exclude_unset=True, exclude={"actor_name"})
        for field in _TRACKED_FIELDS:
            if field in payload:
                old = getattr(incident, field)
                new = payload[field]
                if old != new:
                    changes[field] = (old, new)
                    setattr(incident, field, new)

        if not changes:
            return incident

        self._history.record_changes(incident, changes, actor=actor)
        self._emit_field_timeline(incident, changes, actor)
        self._log.log(
            incident, "updated", message=", ".join(changes), actor=actor
        )
        # Keep the primary location in sync when the address/coords change.
        if {"address", "latitude", "longitude"} & changes.keys():
            self._sync_primary_location(incident)

        await self._session.flush()
        return await self._require(incident_id)

    # ------------------------------------------------------- status change
    async def change_status(
        self, incident_id: UUID, data: StatusChangeRequest
    ) -> Incident:
        incident = await self.get(incident_id)
        actor = Actor(name=data.actor_name)
        current = incident.status
        target = data.status

        if current == target:
            raise ConflictError(f"Incident already in status {target.value}")
        if not can_transition(current, target):
            raise ValidationError(str(InvalidTransitionError(current, target)))

        incident.status = target
        self._apply_status_timestamps(incident, target)
        self._history.record(
            incident, "status", current, target, actor=actor, note=data.note
        )
        self._timeline.record(
            incident,
            TimelineEventType.STATUS_CHANGED,
            f"Статус изменён: {current.value} → {target.value}",
            detail=data.note,
            actor=actor,
        )
        self._emit_status_milestones(incident, target, actor)
        self._log.log(
            incident, "status_changed", message=target.value, actor=actor
        )

        await self._session.flush()
        return await self._require(incident_id)

    # ---------------------------------------------------------- comments
    async def add_comment(
        self, incident_id: UUID, data: CommentCreate
    ) -> Incident:
        incident = await self.get(incident_id)
        actor = Actor(name=data.author_name)
        incident.comments.append(
            IncidentComment(author_name=data.author_name, text=data.text)
        )
        self._timeline.record(
            incident,
            TimelineEventType.COMMENT_ADDED,
            "Добавлен комментарий",
            detail=data.text[:200],
            actor=actor,
        )
        self._log.log(incident, "comment_added", actor=actor)
        await self._session.flush()
        return await self._require(incident_id)

    # ------------------------------------------------------ assign units
    async def assign_units(
        self, incident_id: UUID, data: AssignUnitsRequest
    ) -> Incident:
        incident = await self.get(incident_id)
        actor = Actor(name=data.actor_name)
        existing = {d.resource_id for d in incident.dispatches if not d.is_deleted}
        added = 0
        for unit in data.units:
            if unit.resource_id in existing:
                continue
            incident.dispatches.append(
                IncidentDispatch(
                    resource_id=unit.resource_id, role=unit.role, note=unit.note
                )
            )
            existing.add(unit.resource_id)
            added += 1
        if data.recommendation_id is not None:
            self._link_recommendation(incident, data.recommendation_id)
        self._timeline.record(
            incident,
            TimelineEventType.UNITS_ASSIGNED,
            f"Назначены подразделения: {added}",
            actor=actor,
            meta={"resource_ids": [str(u.resource_id) for u in data.units]},
        )
        self._log.log(incident, "units_assigned", message=str(added), actor=actor)
        await self._session.flush()
        return await self._require(incident_id)

    # ------------------------------------------- recommendation (Dispatch)
    async def request_recommendation(
        self, incident_id: UUID, *, actor_name: str | None = None
    ) -> Incident:
        """Get a dispatch recommendation via the existing Dispatch Engine.

        Reuses ``DispatchService`` unchanged; the incident must have an incident
        type and coordinates. The resulting recommendation is linked to the card.
        """
        from app.dispatch.schemas.requests import DispatchRequest
        from app.dispatch.services import DispatchService

        incident = await self.get(incident_id)
        actor = Actor(name=actor_name)
        if incident.incident_type_id is None:
            raise ValidationError("Incident has no incident type")
        if incident.latitude is None or incident.longitude is None:
            raise ValidationError("Incident has no coordinates")

        dispatch = DispatchService(self._session)
        response = await dispatch.recommend(
            DispatchRequest(
                incident_id=incident.id,
                incident_type_id=incident.incident_type_id,
                latitude=incident.latitude,
                longitude=incident.longitude,
                address=incident.address,
                danger_level=incident.danger_level,
                object_type=incident.object_type,
            )
        )
        self._link_recommendation(incident, response.recommendation.id)
        self._timeline.record(
            incident,
            TimelineEventType.RECOMMENDATION_REQUESTED,
            "Получена рекомендация по составу сил и средств",
            actor=actor,
            meta={"recommendation_id": str(response.recommendation.id)},
        )
        self._log.log(incident, "recommendation_requested", actor=actor)
        await self._session.flush()
        return await self._require(incident_id)

    # -------------------------------------------------- close / archive
    async def close(
        self, incident_id: UUID, *, actor_name: str | None = None
    ) -> Incident:
        return await self.change_status(
            incident_id,
            StatusChangeRequest(status=IncidentStatus.COMPLETED, actor_name=actor_name),
        )

    async def archive(
        self, incident_id: UUID, *, actor_name: str | None = None
    ) -> Incident:
        return await self.change_status(
            incident_id,
            StatusChangeRequest(status=IncidentStatus.ARCHIVED, actor_name=actor_name),
        )

    # ------------------------------------------------------------ helpers
    def _link_recommendation(self, incident: Incident, recommendation_id: UUID) -> None:
        for link in incident.recommendations:
            link.is_current = False
        incident.recommendations.append(
            IncidentRecommendation(
                recommendation_id=recommendation_id, is_current=True
            )
        )

    def _emit_field_timeline(self, incident: Incident, changes, actor) -> None:
        mapping = {
            "address": (TimelineEventType.ADDRESS_CHANGED, "Изменён адрес"),
            "latitude": (TimelineEventType.ADDRESS_CHANGED, "Изменены координаты"),
            "category": (TimelineEventType.CATEGORY_CHANGED, "Изменена категория"),
            "priority": (TimelineEventType.PRIORITY_CHANGED, "Изменён приоритет"),
        }
        emitted: set[TimelineEventType] = set()
        for field, (event, title) in mapping.items():
            if field in changes and event not in emitted:
                self._timeline.record(incident, event, title, actor=actor)
                emitted.add(event)

    def _emit_status_milestones(self, incident: Incident, target, actor) -> None:
        if target in (IncidentStatus.COMPLETED, IncidentStatus.CANCELLED):
            self._timeline.record(
                incident, TimelineEventType.CLOSED, "Происшествие закрыто", actor=actor
            )
        elif target == IncidentStatus.ARCHIVED:
            self._timeline.record(
                incident, TimelineEventType.ARCHIVED, "Происшествие в архиве",
                actor=actor,
            )

    @staticmethod
    def _apply_status_timestamps(incident: Incident, target: IncidentStatus) -> None:
        now = _now()
        if target == IncidentStatus.CONFIRMED and incident.confirmed_at is None:
            incident.confirmed_at = now
        if target in (IncidentStatus.COMPLETED, IncidentStatus.CANCELLED):
            incident.closed_at = now
        if target == IncidentStatus.ARCHIVED:
            incident.archived_at = now

    @staticmethod
    def _sync_primary_location(incident: Incident) -> None:
        primary = next(
            (
                loc
                for loc in incident.locations
                if loc.is_primary and not loc.is_deleted
            ),
            None,
        )
        if primary is None:
            incident.locations.append(
                IncidentLocation(
                    address=incident.address,
                    latitude=incident.latitude,
                    longitude=incident.longitude,
                    administrative_area_id=incident.administrative_area_id,
                    is_primary=True,
                    source="manual",
                )
            )
        else:
            primary.address = incident.address
            primary.latitude = incident.latitude
            primary.longitude = incident.longitude
            primary.administrative_area_id = incident.administrative_area_id

    async def _require(self, incident_id: UUID) -> Incident:
        incident = await self._repo.get_full(incident_id)
        if incident is None:  # pragma: no cover
            raise NotFoundError("Incident not found")
        return incident

    async def get_by_number(self, number: str) -> Incident:
        stmt = select(Incident).where(Incident.number == number)
        incident = (await self._session.execute(stmt)).scalars().first()
        if incident is None:
            raise NotFoundError("Incident not found")
        return await self.get(incident.id)
