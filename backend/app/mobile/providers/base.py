"""Data-provider interface for the mobile BFF (Stage 19).

The BFF reads operational data through this interface, so the source is
pluggable: an in-memory sample provider (default, dependency-free, used by tests)
or an adapter over the real incident / resource / routing services in
production. Either way the mobile apps only ever see the server-produced DTOs —
they contain no business logic.
"""

from __future__ import annotations

from typing import Protocol

from app.mobile.providers.types import (
    DispatchCard,
    MobileIncident,
    OperationalSummary,
    ResourceLoad,
    Route,
)


class MobileDataProvider(Protocol):
    def list_incidents(self, *, active_only: bool = True) -> list[MobileIncident]: ...
    def get_incident(self, incident_id: str) -> MobileIncident | None: ...
    def list_resources(self) -> list[ResourceLoad]: ...
    def operational_summary(self) -> OperationalSummary: ...
    def get_dispatch(self, unit_id: str) -> DispatchCard | None: ...
    def get_route(self, unit_id: str) -> Route | None: ...
    def unit_contact(self, unit_id: str) -> str | None: ...
