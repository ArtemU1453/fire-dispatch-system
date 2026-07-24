"""ORM models package.

Every concrete model is imported here so that (a) SQLAlchemy's mapper registry
can resolve string-based relationships across modules, and (b) Alembic's
autogenerate sees the full metadata. Adding a new model = create the module and
add it to this aggregation point — no architectural change required.
"""

from app.models.assets import Equipment, Personnel, Station, Vehicle
from app.models.audit import AuditLog
from app.models.base import CatalogEntity, Entity
from app.models.catalog import (
    AvailabilityStatus,
    Capability,
    EquipmentType,
    IncidentType,
    IncidentTypeCapability,
    PersonnelRole,
    ResourceType,
    VehicleType,
)
from app.models.enums import AuditAction, ResourceCategory
from app.models.geo import (
    AdministrativeArea,
    CoverageArea,
    CoverageAreaIncidentType,
    Location,
)
from app.models.history import CoordinateHistory, StatusHistory
from app.models.organization import Organization
from app.models.resource import Resource, ResourceCapability
from app.models.security import Permission, Role, RolePermission, User, UserRole

__all__ = [
    # base
    "Entity",
    "CatalogEntity",
    # enums
    "AuditAction",
    "ResourceCategory",
    # catalog
    "ResourceType",
    "VehicleType",
    "PersonnelRole",
    "EquipmentType",
    "AvailabilityStatus",
    "Capability",
    "IncidentType",
    "IncidentTypeCapability",
    # organization
    "Organization",
    # geo
    "AdministrativeArea",
    "Location",
    "CoverageArea",
    "CoverageAreaIncidentType",
    # core resource
    "Resource",
    "ResourceCapability",
    # specializations
    "Station",
    "Vehicle",
    "Personnel",
    "Equipment",
    # history
    "StatusHistory",
    "CoordinateHistory",
    # security
    "User",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    # audit
    "AuditLog",
]
