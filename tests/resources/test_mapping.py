"""Unit tests for resource-management mapping and status logic (no database)."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from app.resources.models.enums import AssignmentStatus, TechnicalCondition
from app.resources.utils.mapping import (
    status_ref,
    unit_to_response,
    vehicle_to_response,
)


def _status(code="free", operational=True, deployable=True):
    return SimpleNamespace(
        id=uuid4(), code=code, name=code, is_operational=operational,
        is_available_for_dispatch=deployable, color="#fff",
    )


def test_status_ref_maps_flags() -> None:
    ref = status_ref(_status(code="on_scene", deployable=False))
    assert ref is not None
    assert ref.code == "on_scene"
    assert ref.is_available_for_dispatch is False
    assert status_ref(None) is None


def test_unit_availability_follows_status() -> None:
    available = SimpleNamespace(
        id=uuid4(), code="U-1", name="АЦ-1", call_sign=None, station_id=None,
        organization=None, vehicle_resource_id=uuid4(),
        availability_status=_status(deployable=True), is_active=True,
        crews=[], assignments=[], notes=None,
    )
    resp = unit_to_response(available)
    assert resp.is_available is True
    assert resp.crew_count == 0
    assert resp.active_assignment_id is None

    busy = SimpleNamespace(**{**available.__dict__})
    busy.availability_status = _status(code="on_scene", deployable=False)
    assignment = SimpleNamespace(
        id=uuid4(), status=AssignmentStatus.ACTIVE, is_deleted=False
    )
    busy.assignments = [assignment]
    busy.crews = [SimpleNamespace(is_deleted=False)]
    resp2 = unit_to_response(busy)
    assert resp2.is_available is False
    assert resp2.crew_count == 1
    assert resp2.active_assignment_id == assignment.id


def test_vehicle_response_uses_state() -> None:
    vehicle = SimpleNamespace(
        id=uuid4(), code="V-1", name="АЦ", availability_status=_status(),
        organization=None,
        vehicle=SimpleNamespace(
            plate_number="А001", vehicle_type=None, odometer_km=1000
        ),
    )
    state = SimpleNamespace(
        is_available=False, fuel_level_percent=40, mileage_km=1234,
        technical_condition=TechnicalCondition.NEEDS_SERVICE, last_service_at=None,
    )
    resp = vehicle_to_response(vehicle, state)
    assert resp.plate_number == "А001"
    assert resp.fuel_level_percent == 40
    assert resp.mileage_km == 1234
    assert resp.is_available is False
    assert resp.technical_condition is TechnicalCondition.NEEDS_SERVICE
