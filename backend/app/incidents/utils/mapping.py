"""Mapping between incident ORM objects and API schemas."""

from __future__ import annotations

from app.incidents.models.entities import Incident
from app.incidents.schemas.incident import (
    IncidentResponse,
    IncidentSummaryResponse,
)
from app.incidents.validators.state_machine import allowed_targets


def incident_to_response(incident: Incident) -> IncidentResponse:
    response = IncidentResponse.model_validate(incident)
    response.allowed_transitions = sorted(
        allowed_targets(incident.status), key=lambda s: s.value
    )
    # Chronological order for the audit views.
    response.timeline.sort(key=lambda e: e.occurred_at)
    response.history.sort(key=lambda e: e.occurred_at)
    return response


def incident_to_summary(incident: Incident) -> IncidentSummaryResponse:
    return IncidentSummaryResponse.model_validate(incident)
