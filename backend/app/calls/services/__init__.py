"""Call-management application services."""

from __future__ import annotations

from app.calls.services.call_service import CallService
from app.calls.services.incident_linker import CallIncidentLinker

__all__ = ["CallIncidentLinker", "CallService"]
