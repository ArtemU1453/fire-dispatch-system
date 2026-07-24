"""Geospatial reference entities.

- :class:`AdministrativeArea` — territorial hierarchy (region → city → district)
  with a polygon boundary.
- :class:`Location` — a reusable, structured address/place with a point.
- :class:`CoverageArea` — a resource's (station's) area of responsibility, with
  the incident types it serves via :class:`CoverageAreaIncidentType`.

Resources carry their own live point via ``GeoPointMixin``; these entities model
*fixed* geography (addresses, boundaries, coverage), which is why they are
separate — a resource references its registered :class:`Location`, while its
current position is tracked directly on the resource.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from geoalchemy2 import Geometry
from geoalchemy2.elements import WKBElement
from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Entity
from app.models.mixins import SRID, GeoPointMixin

if TYPE_CHECKING:
    from app.models.catalog import IncidentType
    from app.models.resource import Resource


class AdministrativeArea(Entity):
    """A territorial administrative unit with an optional polygon boundary."""

    __tablename__ = "administrative_areas"
    __table_args__ = (
        UniqueConstraint("code", name="uq_administrative_area_code"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("administrative_areas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    boundary: Mapped[WKBElement | None] = mapped_column(
        Geometry(geometry_type="MULTIPOLYGON", srid=SRID, spatial_index=True),
        nullable=True,
    )

    parent: Mapped[AdministrativeArea | None] = relationship(
        remote_side="AdministrativeArea.id", back_populates="children"
    )
    children: Mapped[list[AdministrativeArea]] = relationship(back_populates="parent")
    locations: Mapped[list[Location]] = relationship(
        back_populates="administrative_area"
    )


class Location(Entity, GeoPointMixin):
    """A structured address / named place with a point geometry."""

    __tablename__ = "locations"

    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    administrative_area_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("administrative_areas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    administrative_area: Mapped[AdministrativeArea | None] = relationship(
        back_populates="locations"
    )
    resources: Mapped[list[Resource]] = relationship(back_populates="location")


class CoverageArea(Entity):
    """An area of responsibility (response zone) for a resource/station."""

    __tablename__ = "coverage_areas"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"), nullable=True, index=True
    )
    administrative_area_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("administrative_areas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    priority: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    area: Mapped[WKBElement | None] = mapped_column(
        Geometry(geometry_type="MULTIPOLYGON", srid=SRID, spatial_index=True),
        nullable=True,
    )

    resource: Mapped[Resource | None] = relationship(back_populates="coverage_areas")
    administrative_area: Mapped[AdministrativeArea | None] = relationship()
    incident_type_links: Mapped[list[CoverageAreaIncidentType]] = relationship(
        back_populates="coverage_area"
    )


class CoverageAreaIncidentType(Entity):
    """Junction: which incident types a :class:`CoverageArea` serves."""

    __tablename__ = "coverage_area_incident_types"
    __table_args__ = (
        UniqueConstraint(
            "coverage_area_id",
            "incident_type_id",
            name="uq_coverage_area_incident_type",
        ),
    )

    coverage_area_id: Mapped[UUID] = mapped_column(
        ForeignKey("coverage_areas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    incident_type_id: Mapped[UUID] = mapped_column(
        ForeignKey("incident_types.id", ondelete="CASCADE"), nullable=False, index=True
    )
    priority: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)

    coverage_area: Mapped[CoverageArea] = relationship(
        back_populates="incident_type_links"
    )
    incident_type: Mapped[IncidentType] = relationship()
