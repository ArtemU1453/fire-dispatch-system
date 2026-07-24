"""Schemas for the resource specialization tables."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from app.schemas.common import ResponseBase, SchemaBase

# ------------------------------------------------------------------- station --


class StationCreate(SchemaBase):
    resource_id: UUID
    station_number: str | None = None
    garage_capacity: int | None = None
    staff_capacity: int | None = None
    is_round_the_clock: bool = True


class StationUpdate(SchemaBase):
    station_number: str | None = None
    garage_capacity: int | None = None
    staff_capacity: int | None = None
    is_round_the_clock: bool | None = None


class StationResponse(ResponseBase):
    resource_id: UUID
    station_number: str | None = None
    garage_capacity: int | None = None
    staff_capacity: int | None = None
    is_round_the_clock: bool


# ------------------------------------------------------------------- vehicle --


class VehicleCreate(SchemaBase):
    resource_id: UUID
    vehicle_type_id: UUID
    plate_number: str | None = None
    crew_capacity: int | None = None
    water_capacity_l: int | None = None
    foam_capacity_l: int | None = None
    pump_capacity_l_min: int | None = None
    ladder_height_m: float | None = None
    year_manufactured: int | None = None
    odometer_km: int | None = None


class VehicleUpdate(SchemaBase):
    vehicle_type_id: UUID | None = None
    plate_number: str | None = None
    crew_capacity: int | None = None
    water_capacity_l: int | None = None
    foam_capacity_l: int | None = None
    pump_capacity_l_min: int | None = None
    ladder_height_m: float | None = None
    year_manufactured: int | None = None
    odometer_km: int | None = None


class VehicleResponse(ResponseBase):
    resource_id: UUID
    vehicle_type_id: UUID
    plate_number: str | None = None
    crew_capacity: int | None = None
    water_capacity_l: int | None = None
    foam_capacity_l: int | None = None
    pump_capacity_l_min: int | None = None
    ladder_height_m: float | None = None
    year_manufactured: int | None = None
    odometer_km: int | None = None


# ----------------------------------------------------------------- personnel --


class PersonnelCreate(SchemaBase):
    resource_id: UUID
    personnel_role_id: UUID
    first_name: str
    last_name: str
    middle_name: str | None = None
    rank: str | None = None
    badge_number: str | None = None
    phone: str | None = None
    hired_at: date | None = None


class PersonnelUpdate(SchemaBase):
    personnel_role_id: UUID | None = None
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None
    rank: str | None = None
    badge_number: str | None = None
    phone: str | None = None
    hired_at: date | None = None


class PersonnelResponse(ResponseBase):
    resource_id: UUID
    personnel_role_id: UUID
    first_name: str
    last_name: str
    middle_name: str | None = None
    rank: str | None = None
    badge_number: str | None = None
    phone: str | None = None
    hired_at: date | None = None


# ----------------------------------------------------------------- equipment --


class EquipmentCreate(SchemaBase):
    resource_id: UUID
    equipment_type_id: UUID
    serial_number: str | None = None
    inventory_number: str | None = None
    quantity: int = 1
    last_service_at: date | None = None


class EquipmentUpdate(SchemaBase):
    equipment_type_id: UUID | None = None
    serial_number: str | None = None
    inventory_number: str | None = None
    quantity: int | None = None
    last_service_at: date | None = None


class EquipmentResponse(ResponseBase):
    resource_id: UUID
    equipment_type_id: UUID
    serial_number: str | None = None
    inventory_number: str | None = None
    quantity: int
    last_service_at: date | None = None
