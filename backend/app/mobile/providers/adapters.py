"""Production data-provider seam (Stage 19).

In production the mobile BFF is backed by the **real** operational services
(incidents, resources, routing, analytics) instead of the sample provider. This
module is the documented seam for that wiring: :class:`RealServiceDataProvider`
implements :class:`MobileDataProvider` by delegating to those services over a
database session.

It is intentionally a scaffold — the default provider is the in-memory sample
one, and tests never touch a database — so the mobile module stays isolated and
CI-green. To go live, an operator implements each method by mapping the existing
services' results into the mobile DTOs (the mapping is described in
``docs/mobile.md``); no endpoint or app code changes.
"""

from __future__ import annotations

from app.mobile.providers.types import (
    DispatchCard,
    MobileIncident,
    OperationalSummary,
    ResourceLoad,
    Route,
)


class RealServiceDataProvider:
    """Adapter over the live services (production seam; not wired by default)."""

    def __init__(self, session: object) -> None:
        # ``session`` is an AsyncSession in production; typed loosely so importing
        # this seam never drags database dependencies into the mobile module.
        self._session = session

    def _not_wired(self, what: str) -> RuntimeError:
        return RuntimeError(
            f"RealServiceDataProvider.{what} is a production seam and is not wired "
            "in this build; see docs/mobile.md for the mapping to the existing "
            "incident/resource/routing services."
        )

    def list_incidents(self, *, active_only: bool = True) -> list[MobileIncident]:
        raise self._not_wired("list_incidents")

    def get_incident(self, incident_id: str) -> MobileIncident | None:
        raise self._not_wired("get_incident")

    def list_resources(self) -> list[ResourceLoad]:
        raise self._not_wired("list_resources")

    def operational_summary(self) -> OperationalSummary:
        raise self._not_wired("operational_summary")

    def get_dispatch(self, unit_id: str) -> DispatchCard | None:
        raise self._not_wired("get_dispatch")

    def get_route(self, unit_id: str) -> Route | None:
        raise self._not_wired("get_route")

    def unit_contact(self, unit_id: str) -> str | None:
        raise self._not_wired("unit_contact")
