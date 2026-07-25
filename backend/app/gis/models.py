"""GIS domain models — the geographic gazetteer and geocoding records.

These extend the Stage-2 ORM foundation (``Entity`` base: UUID PK, timestamps,
soft-delete) — the previous architecture is reused, not changed. The address
hierarchy (Region → District → Settlement → Street → Building) is the geocoding
gazetteer; it complements (and can optionally reference) the Stage-2
``administrative_areas`` used for dispatch coverage, without duplicating it.

Spatial columns use PostGIS ``Geometry(Point/Polygon, 4326)`` with GiST indexes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from geoalchemy2 import Geometry
from geoalchemy2.elements import WKBElement
from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Entity
from app.models.mixins import SRID, GeoPointMixin

if TYPE_CHECKING:
    from app.models.geo import AdministrativeArea


class Region(Entity):
    """Top-level administrative region (область/республика/край)."""

    __tablename__ = "gis_regions"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    # Optional bridge to the Stage-2 dispatch-territory hierarchy.
    administrative_area_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("administrative_areas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    boundary: Mapped[WKBElement | None] = mapped_column(
        Geometry(geometry_type="POLYGON", srid=SRID, spatial_index=True),
        nullable=True,
    )

    administrative_area: Mapped[AdministrativeArea | None] = relationship()
    districts: Mapped[list[District]] = relationship(back_populates="region")


class District(Entity):
    """Administrative district (район) within a region."""

    __tablename__ = "gis_districts"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    region_id: Mapped[UUID] = mapped_column(
        ForeignKey("gis_regions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    boundary: Mapped[WKBElement | None] = mapped_column(
        Geometry(geometry_type="POLYGON", srid=SRID, spatial_index=True),
        nullable=True,
    )

    region: Mapped[Region] = relationship(back_populates="districts")
    settlements: Mapped[list[Settlement]] = relationship(back_populates="district")


class Settlement(Entity, GeoPointMixin):
    """Populated place (город/посёлок/село/деревня)."""

    __tablename__ = "gis_settlements"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    settlement_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    district_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("gis_districts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    region_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("gis_regions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    boundary: Mapped[WKBElement | None] = mapped_column(
        Geometry(geometry_type="POLYGON", srid=SRID, spatial_index=True),
        nullable=True,
    )

    district: Mapped[District | None] = relationship(back_populates="settlements")
    streets: Mapped[list[Street]] = relationship(back_populates="settlement")


class Street(Entity):
    """A street / thoroughfare within a settlement."""

    __tablename__ = "gis_streets"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    street_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    settlement_id: Mapped[UUID] = mapped_column(
        ForeignKey("gis_settlements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    settlement: Mapped[Settlement] = relationship(back_populates="streets")
    buildings: Mapped[list[Building]] = relationship(back_populates="street")


class Building(Entity, GeoPointMixin):
    """A building / house with a house number and a point location."""

    __tablename__ = "gis_buildings"
    __table_args__ = (
        UniqueConstraint(
            "street_id", "house_number", "block", name="uq_building_address"
        ),
    )

    house_number: Mapped[str] = mapped_column(String(32), nullable=False)
    block: Mapped[str | None] = mapped_column(String(32), nullable=True)
    building: Mapped[str | None] = mapped_column(String(32), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    street_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("gis_streets.id", ondelete="SET NULL"), nullable=True, index=True
    )

    street: Mapped[Street | None] = relationship(back_populates="buildings")


class Coordinate(Entity, GeoPointMixin):
    """A stored coordinate (point) with its source and accuracy.

    A reusable spatial value: an :class:`Address` references the coordinate it
    was geocoded to, and other records can point at the same location.
    """

    __tablename__ = "gis_coordinates"

    srid: Mapped[int] = mapped_column(Integer, server_default=str(SRID), nullable=False)
    accuracy: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)


class Address(Entity, GeoPointMixin):
    """A geocoded address record linking raw/normalized text to a location.

    Holds the free-text input, the normalized form, the resolved structured
    components (via nullable FKs into the gazetteer) and the coordinate. This is
    what the geocoding service persists and what nearest-resource search (next
    stage) will read from.
    """

    __tablename__ = "gis_addresses"

    raw_address: Mapped[str] = mapped_column(String(1024), nullable=False)
    normalized_address: Mapped[str | None] = mapped_column(
        String(1024), nullable=True, index=True
    )
    formatted_address: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    country: Mapped[str | None] = mapped_column(String(128), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    house_number: Mapped[str | None] = mapped_column(String(32), nullable=True)

    accuracy: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_validated: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )

    region_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("gis_regions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    district_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("gis_districts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    settlement_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("gis_settlements.id", ondelete="SET NULL"), nullable=True, index=True
    )
    street_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("gis_streets.id", ondelete="SET NULL"), nullable=True, index=True
    )
    building_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("gis_buildings.id", ondelete="SET NULL"), nullable=True, index=True
    )
    coordinate_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("gis_coordinates.id", ondelete="SET NULL"), nullable=True, index=True
    )

    region: Mapped[Region | None] = relationship()
    district: Mapped[District | None] = relationship()
    settlement: Mapped[Settlement | None] = relationship()
    street: Mapped[Street | None] = relationship()
    building: Mapped[Building | None] = relationship()
    coordinate: Mapped[Coordinate | None] = relationship()


class GeocodingLog(Entity):
    """Audit of every geocoding / reverse-geocoding request (requirement 11)."""

    __tablename__ = "gis_geocoding_logs"

    operation: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    query: Mapped[str] = mapped_column(String(1024), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    result_count: Mapped[int] = mapped_column(
        Integer, server_default="0", nullable=False
    )
    response_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    from_cache: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
