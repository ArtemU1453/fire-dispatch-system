"""Call → Incident linking — the decision logic isolated in its own service.

Section 6 of the stage requires that every call either **creates a new incident
card** or is **attached to an existing one**, and that this choice live in a
dedicated service. ``CallIncidentLinker`` owns exactly that: it builds an
incident from a call (reusing the Stage-9 ``IncidentService`` unchanged) or links
an existing incident, and records the ``CallIncidentLink`` on the call.

The Incident Management module is **not modified** — only its public service and
schemas are consumed.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.calls.models.entities import Call, CallIncidentLink
from app.calls.models.enums import CallLinkType, CallSource
from app.calls.utils.actor import Actor
from app.core.exceptions import ValidationError
from app.incidents.models.entities import Incident
from app.incidents.models.enums import (
    IncidentCategory,
    IncidentPriority,
    IncidentSource,
)
from app.incidents.schemas.incident import IncidentCreate
from app.incidents.services import IncidentService

# How a call's telephony source maps onto the incident's report source.
_SOURCE_MAP = {
    CallSource.PHONE: IncidentSource.PHONE,
    CallSource.MOBILE: IncidentSource.PHONE,
    CallSource.SIP: IncidentSource.PHONE,
    CallSource.WEBRTC: IncidentSource.PHONE,
    CallSource.RADIO: IncidentSource.RADIO,
    CallSource.MANUAL: IncidentSource.MANUAL,
    CallSource.OTHER: IncidentSource.OTHER,
}


class CallIncidentLinker:
    """Creates or links incidents for calls (isolated selection logic)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._incidents = IncidentService(session)

    async def create_incident_for_call(
        self,
        call: Call,
        *,
        incident_type_id: UUID | None = None,
        category: IncidentCategory = IncidentCategory.OTHER,
        priority: IncidentPriority = IncidentPriority.NORMAL,
        title: str | None = None,
        description: str | None = None,
        address: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        actor: Actor | None = None,
    ) -> Incident:
        """Create a brand-new incident card from the call's data."""
        actor = actor or Actor()
        incident = await self._incidents.create(
            IncidentCreate(
                incident_type_id=incident_type_id,
                category=category,
                source=_SOURCE_MAP.get(call.source, IncidentSource.PHONE),
                priority=priority,
                title=title or (call.notes or None),
                description=description or call.notes,
                address=address or call.address_hint,
                latitude=latitude,
                longitude=longitude,
                reporter_name=call.caller_name,
                reporter_contact=call.caller_number,
                actor_name=actor.name,
            )
        )
        self._attach(call, incident.id, CallLinkType.CREATED)
        return incident

    async def link_existing(
        self, call: Call, incident_id: UUID, *, actor: Actor | None = None
    ) -> Incident:
        """Attach the call to an already-existing incident card."""
        incident = await self._incidents.get(incident_id)  # 404 if missing
        self._attach(call, incident.id, CallLinkType.LINKED)
        return incident

    def _attach(
        self, call: Call, incident_id: UUID, link_type: CallLinkType
    ) -> None:
        """Record the link on the call and set the primary incident."""
        already = {
            link.incident_id for link in call.links if not link.is_deleted
        }
        is_primary = call.incident_id is None
        if incident_id not in already:
            call.links.append(
                CallIncidentLink(
                    incident_id=incident_id,
                    link_type=link_type,
                    is_primary=is_primary,
                )
            )
        if is_primary:
            call.incident_id = incident_id

    @staticmethod
    def require_choice(
        incident_id: UUID | None, *, create: bool
    ) -> None:
        """Validate that exactly one of link-existing / create-new was chosen."""
        if incident_id is not None and create:
            raise ValidationError(
                "Provide either incident_id (link existing) or create=true, "
                "not both"
            )
        if incident_id is None and not create:
            raise ValidationError(
                "Provide incident_id to link, or create=true to create a new "
                "incident"
            )
