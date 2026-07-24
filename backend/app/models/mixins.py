"""Reusable model mixins for geospatial data.

``GeoPointMixin`` gives a table the trio required by the spec — ``latitude``,
``longitude`` and a PostGIS ``geometry(Point, 4326)`` — in one place (DRY). The
scalar lat/lon are kept alongside the geometry as a convenience for clients and
simple filters; ``geom`` is the authoritative spatial value.

``spatial_index=True`` asks PostGIS/GeoAlchemy2 to create a GiST index for the
column; the GeoAlchemy2 Alembic integration (see ``migrations/env.py``) emits
that index into migrations so spatial indexes are versioned like any other.
"""

from __future__ import annotations

from geoalchemy2 import Geometry
from geoalchemy2.elements import WKBElement
from sqlalchemy import Float
from sqlalchemy.orm import Mapped, mapped_column

# Spatial Reference System: WGS-84 (GPS lat/lon).
SRID = 4326


class GeoPointMixin:
    """Adds ``latitude`` / ``longitude`` scalars and a GiST-indexed ``geom``."""

    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    geom: Mapped[WKBElement | None] = mapped_column(
        Geometry(geometry_type="POINT", srid=SRID, spatial_index=True),
        nullable=True,
    )
