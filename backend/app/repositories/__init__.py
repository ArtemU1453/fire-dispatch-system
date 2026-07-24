"""Repositories package (Repository Pattern).

Exposes the generic base classes plus a concrete repository per domain model.
New repositories are added in :mod:`app.repositories.entities` without altering
the interface the service layer depends on.
"""

from app.repositories.base import (
    AbstractRepository,
    Page,
    QuerySpec,
    SqlAlchemyRepository,
)
from app.repositories.entities import (
    AdministrativeAreaRepository,
    AuditLogRepository,
    AvailabilityStatusRepository,
    CapabilityRepository,
    CoordinateHistoryRepository,
    CoverageAreaIncidentTypeRepository,
    CoverageAreaRepository,
    EquipmentRepository,
    EquipmentTypeRepository,
    IncidentTypeCapabilityRepository,
    IncidentTypeRepository,
    LocationRepository,
    OrganizationRepository,
    PermissionRepository,
    PersonnelRepository,
    PersonnelRoleRepository,
    ResourceCapabilityRepository,
    ResourceRepository,
    ResourceTypeRepository,
    RolePermissionRepository,
    RoleRepository,
    StationRepository,
    StatusHistoryRepository,
    UserRepository,
    UserRoleRepository,
    VehicleRepository,
    VehicleTypeRepository,
)

__all__ = [
    # base
    "AbstractRepository",
    "SqlAlchemyRepository",
    "QuerySpec",
    "Page",
    # concrete
    "ResourceRepository",
    "ResourceTypeRepository",
    "ResourceCapabilityRepository",
    "CapabilityRepository",
    "OrganizationRepository",
    "StationRepository",
    "VehicleRepository",
    "VehicleTypeRepository",
    "PersonnelRepository",
    "PersonnelRoleRepository",
    "EquipmentRepository",
    "EquipmentTypeRepository",
    "AvailabilityStatusRepository",
    "LocationRepository",
    "AdministrativeAreaRepository",
    "CoverageAreaRepository",
    "CoverageAreaIncidentTypeRepository",
    "IncidentTypeRepository",
    "IncidentTypeCapabilityRepository",
    "StatusHistoryRepository",
    "CoordinateHistoryRepository",
    "UserRepository",
    "RoleRepository",
    "PermissionRepository",
    "UserRoleRepository",
    "RolePermissionRepository",
    "AuditLogRepository",
]
