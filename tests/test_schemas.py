"""Tests that every entity exposes Create/Update/Response schemas."""

from __future__ import annotations

import importlib

import pytest

from app.schemas.common import ResponseBase

# Entities and the schema module they live in.
ENTITY_MODULES = {
    "ResourceType": "catalog",
    "VehicleType": "catalog",
    "PersonnelRole": "catalog",
    "EquipmentType": "catalog",
    "AvailabilityStatus": "catalog",
    "Capability": "catalog",
    "IncidentType": "catalog",
    "IncidentTypeCapability": "catalog",
    "Organization": "organization",
    "AdministrativeArea": "geo",
    "Location": "geo",
    "CoverageArea": "geo",
    "CoverageAreaIncidentType": "geo",
    "Resource": "resource",
    "ResourceCapability": "resource",
    "Station": "assets",
    "Vehicle": "assets",
    "Personnel": "assets",
    "Equipment": "assets",
    "StatusHistory": "history",
    "CoordinateHistory": "history",
    "User": "security",
    "Role": "security",
    "Permission": "security",
    "UserRole": "security",
    "RolePermission": "security",
    "AuditLog": "audit",
}


@pytest.mark.parametrize("entity, module", sorted(ENTITY_MODULES.items()))
def test_entity_has_crud_schemas(entity: str, module: str) -> None:
    mod = importlib.import_module(f"app.schemas.{module}")
    for suffix in ("Create", "Update", "Response"):
        assert hasattr(mod, f"{entity}{suffix}"), f"missing {entity}{suffix}"


@pytest.mark.parametrize("entity, module", sorted(ENTITY_MODULES.items()))
def test_response_carries_identity_and_audit_fields(entity: str, module: str) -> None:
    mod = importlib.import_module(f"app.schemas.{module}")
    response = getattr(mod, f"{entity}Response")
    assert issubclass(response, ResponseBase)
    fields = set(response.model_fields)
    assert {"id", "created_at", "updated_at", "is_deleted"} <= fields, entity
