"""Concrete repositories for every domain model.

Each is a thin subclass of :class:`SqlAlchemyRepository` binding a ``model`` — it
inherits full CRUD + filter/sort/paginate behaviour (DRY). Add per-entity query
methods here later without changing the base or the service layer.
"""

from __future__ import annotations

from app.models import (
    AdministrativeArea,
    AuditLog,
    AvailabilityStatus,
    Capability,
    CoordinateHistory,
    CoverageArea,
    CoverageAreaIncidentType,
    Equipment,
    EquipmentType,
    IncidentType,
    IncidentTypeCapability,
    Location,
    Organization,
    Permission,
    Personnel,
    PersonnelRole,
    Resource,
    ResourceCapability,
    ResourceType,
    Role,
    RolePermission,
    Station,
    StatusHistory,
    User,
    UserRole,
    Vehicle,
    VehicleType,
)
from app.repositories.base import SqlAlchemyRepository


class ResourceRepository(SqlAlchemyRepository[Resource]):
    model = Resource


class ResourceTypeRepository(SqlAlchemyRepository[ResourceType]):
    model = ResourceType


class ResourceCapabilityRepository(SqlAlchemyRepository[ResourceCapability]):
    model = ResourceCapability


class CapabilityRepository(SqlAlchemyRepository[Capability]):
    model = Capability


class OrganizationRepository(SqlAlchemyRepository[Organization]):
    model = Organization


class StationRepository(SqlAlchemyRepository[Station]):
    model = Station


class VehicleRepository(SqlAlchemyRepository[Vehicle]):
    model = Vehicle


class VehicleTypeRepository(SqlAlchemyRepository[VehicleType]):
    model = VehicleType


class PersonnelRepository(SqlAlchemyRepository[Personnel]):
    model = Personnel


class PersonnelRoleRepository(SqlAlchemyRepository[PersonnelRole]):
    model = PersonnelRole


class EquipmentRepository(SqlAlchemyRepository[Equipment]):
    model = Equipment


class EquipmentTypeRepository(SqlAlchemyRepository[EquipmentType]):
    model = EquipmentType


class AvailabilityStatusRepository(SqlAlchemyRepository[AvailabilityStatus]):
    model = AvailabilityStatus


class LocationRepository(SqlAlchemyRepository[Location]):
    model = Location


class AdministrativeAreaRepository(SqlAlchemyRepository[AdministrativeArea]):
    model = AdministrativeArea


class CoverageAreaRepository(SqlAlchemyRepository[CoverageArea]):
    model = CoverageArea


class CoverageAreaIncidentTypeRepository(
    SqlAlchemyRepository[CoverageAreaIncidentType]
):
    model = CoverageAreaIncidentType


class IncidentTypeRepository(SqlAlchemyRepository[IncidentType]):
    model = IncidentType


class IncidentTypeCapabilityRepository(SqlAlchemyRepository[IncidentTypeCapability]):
    model = IncidentTypeCapability


class StatusHistoryRepository(SqlAlchemyRepository[StatusHistory]):
    model = StatusHistory


class CoordinateHistoryRepository(SqlAlchemyRepository[CoordinateHistory]):
    model = CoordinateHistory


class UserRepository(SqlAlchemyRepository[User]):
    model = User


class RoleRepository(SqlAlchemyRepository[Role]):
    model = Role


class PermissionRepository(SqlAlchemyRepository[Permission]):
    model = Permission


class UserRoleRepository(SqlAlchemyRepository[UserRole]):
    model = UserRole


class RolePermissionRepository(SqlAlchemyRepository[RolePermission]):
    model = RolePermission


class AuditLogRepository(SqlAlchemyRepository[AuditLog]):
    model = AuditLog
