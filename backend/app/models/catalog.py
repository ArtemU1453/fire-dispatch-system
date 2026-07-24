"""Catalog (lookup) tables — the extension mechanism of the system.

Every classification is a table of rows, not a code enum, so new resource types,
vehicle types, roles, statuses, capabilities and incident types are added as
data without schema or code changes (Open/Closed Principle at the data layer).
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import CatalogEntity, Entity
from app.models.enums import ResourceCategory

if TYPE_CHECKING:
    from app.models.assets import Equipment, Personnel, Vehicle
    from app.models.resource import Resource


class ResourceType(CatalogEntity):
    """Kind of resource (fire station, engine, hydrant, hospital, …).

    ``category`` ties the type to an optional specialization table; most new
    types need only a new row here.
    """

    __tablename__ = "resource_types"

    category: Mapped[ResourceCategory] = mapped_column(
        Enum(ResourceCategory, name="resource_category"),
        nullable=False,
        index=True,
    )

    resources: Mapped[list[Resource]] = relationship(back_populates="resource_type")


class VehicleType(CatalogEntity):
    """Class of apparatus (pumper, aerial ladder, rescue, tanker, …)."""

    __tablename__ = "vehicle_types"

    vehicles: Mapped[list[Vehicle]] = relationship(back_populates="vehicle_type")


class PersonnelRole(CatalogEntity):
    """Functional role of a person (commander, driver, firefighter, medic, …)."""

    __tablename__ = "personnel_roles"

    personnel: Mapped[list[Personnel]] = relationship(back_populates="role")


class EquipmentType(CatalogEntity):
    """Class of equipment (hose, breathing apparatus, hydraulic tool, …)."""

    __tablename__ = "equipment_types"

    equipment: Mapped[list[Equipment]] = relationship(back_populates="equipment_type")


class AvailabilityStatus(CatalogEntity):
    """Operational status a resource can be in (available, en route, …).

    Flags let dispatch logic (added later) decide which statuses count as
    deployable without hard-coding status codes.
    """

    __tablename__ = "availability_statuses"

    is_operational: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), nullable=False
    )
    is_available_for_dispatch: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    color: Mapped[str | None] = mapped_column(String(16), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)


class Capability(CatalogEntity):
    """A discrete function a resource can provide or an incident can require.

    Examples: ``fire_suppression``, ``aerial_rescue``, ``water_supply``,
    ``medical_aid``. Shared vocabulary linking resources to incident needs.
    """

    __tablename__ = "capabilities"

    resource_links: Mapped[list[ResourceCapability]] = relationship(
        back_populates="capability"
    )
    incident_links: Mapped[list[IncidentTypeCapability]] = relationship(
        back_populates="capability"
    )


class IncidentType(CatalogEntity):
    """Category of incident (structure fire, road accident, gas leak, …).

    Self-referential so sub-types can be nested. Its required capabilities are
    defined via :class:`IncidentTypeCapability`.
    """

    __tablename__ = "incident_types"

    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("incident_types.id", ondelete="SET NULL"), nullable=True, index=True
    )

    parent: Mapped[IncidentType | None] = relationship(
        remote_side="IncidentType.id", back_populates="children"
    )
    children: Mapped[list[IncidentType]] = relationship(back_populates="parent")
    required_capabilities: Mapped[list[IncidentTypeCapability]] = relationship(
        back_populates="incident_type"
    )


class IncidentTypeCapability(Entity):
    """Junction: capabilities required to handle an :class:`IncidentType`.

    ``min_quantity`` expresses how many resources providing the capability are
    needed — the basis for future automated dispatch matching.
    """

    __tablename__ = "incident_type_capabilities"
    __table_args__ = (
        UniqueConstraint(
            "incident_type_id", "capability_id", name="uq_incident_type_capability"
        ),
    )

    incident_type_id: Mapped[UUID] = mapped_column(
        ForeignKey("incident_types.id", ondelete="CASCADE"), nullable=False, index=True
    )
    capability_id: Mapped[UUID] = mapped_column(
        ForeignKey("capabilities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    min_quantity: Mapped[int] = mapped_column(
        Integer, server_default="1", nullable=False
    )

    incident_type: Mapped[IncidentType] = relationship(
        back_populates="required_capabilities"
    )
    capability: Mapped[Capability] = relationship(back_populates="incident_links")


# Imported at end to avoid a circular import while keeping type hints resolvable.
from app.models.resource import ResourceCapability  # noqa: E402
