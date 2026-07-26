"""In-memory sample data provider (Stage 19).

The default provider: deterministic, dependency-free operational data so the
mobile BFF and its tests run without a database. In production this is replaced
by an adapter over the real services (see ``adapters.py``) via dependency
injection — no endpoint or app code changes.
"""

from __future__ import annotations

from app.mobile.providers.types import (
    DispatchCard,
    MobileIncident,
    OperationalSummary,
    ResourceLoad,
    Route,
    RoutePoint,
)


class SampleDataProvider:
    """A small, realistic operational snapshot held in memory."""

    def __init__(self) -> None:
        self._incidents: dict[str, MobileIncident] = {
            "INC-1001": MobileIncident(
                id="INC-1001", category="fire", priority="high", status="dispatched",
                address="ул. Ленина, 12", description="Пожар в жилом доме, 3 этаж",
                lat=55.751, lon=37.618, created_at="2026-07-26T09:00:00Z",
                recommended_units=["АЦ-1", "АЦ-2"], assigned_unit_ids=["U1"],
            ),
            "INC-1002": MobileIncident(
                id="INC-1002", category="traffic_accident", priority="medium",
                status="pending", address="Проспект Мира, 45",
                description="ДТП, два автомобиля", lat=55.780, lon=37.633,
                created_at="2026-07-26T09:05:00Z",
                recommended_units=["АСМ-1"], assigned_unit_ids=[],
            ),
        }
        self._resources: dict[str, ResourceLoad] = {
            "U1": ResourceLoad(
                "U1", "АЦ-1", "fire", "busy", True, 55.749, 37.620
            ),
            "U2": ResourceLoad(
                "U2", "АЦ-2", "fire", "available", False, 55.760, 37.610
            ),
            "U3": ResourceLoad(
                "U3", "АСМ-1", "rescue", "available", False, 55.770, 37.640
            ),
        }
        self._contacts = {"U1": "+7 495 000-00-01", "U2": "+7 495 000-00-02"}
        self._assignment = {"U1": "INC-1001"}

    def list_incidents(self, *, active_only: bool = True) -> list[MobileIncident]:
        items = list(self._incidents.values())
        if active_only:
            items = [i for i in items if i.status in ("pending", "dispatched")]
        return sorted(items, key=lambda i: i.created_at)

    def get_incident(self, incident_id: str) -> MobileIncident | None:
        return self._incidents.get(incident_id)

    def list_resources(self) -> list[ResourceLoad]:
        return sorted(self._resources.values(), key=lambda r: r.unit_id)

    def operational_summary(self) -> OperationalSummary:
        res = self._resources.values()
        return OperationalSummary(
            active_incidents=len(self.list_incidents(active_only=True)),
            available_units=sum(1 for r in res if not r.busy),
            busy_units=sum(1 for r in res if r.busy),
            calls_today=len(self._incidents),
        )

    def get_dispatch(self, unit_id: str) -> DispatchCard | None:
        incident_id = self._assignment.get(unit_id)
        if incident_id is None:
            return None
        inc = self._incidents[incident_id]
        return DispatchCard(
            incident_id=inc.id,
            address=inc.address,
            description=inc.description,
            category=inc.category,
            priority=inc.priority,
            recommended_composition=list(inc.recommended_units),
            contact=self._contacts.get(unit_id),
            lat=inc.lat,
            lon=inc.lon,
        )

    def get_route(self, unit_id: str) -> Route | None:
        incident_id = self._assignment.get(unit_id)
        unit = self._resources.get(unit_id)
        if incident_id is None or unit is None or unit.lat is None:
            return None
        inc = self._incidents[incident_id]
        if inc.lat is None or inc.lon is None:
            return None
        # A simple two-point route; the real provider uses the routing service.
        return Route(
            points=[
                RoutePoint(unit.lat, unit.lon),
                RoutePoint(inc.lat, inc.lon),
            ],
            distance_km=3.2,
            eta_seconds=280.0,
        )

    def unit_contact(self, unit_id: str) -> str | None:
        return self._contacts.get(unit_id)
