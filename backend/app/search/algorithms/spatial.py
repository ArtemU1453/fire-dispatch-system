"""PostGIS expression builders for spatial search.

Pure helpers returning SQLAlchemy/PostGIS expressions — no session, no I/O — so
the :class:`SearchEngine` composes them into a single statement (minimizing round
trips). They rely on the GiST spatial index on ``resources.geom``:

- ``ST_DWithin`` (geography)  → indexed radius filter, metric.
- ``ST_Distance`` (geography) → exact distance in metres (for value + sort).
- ``geom <-> point``          → KNN ordering (index-assisted nearest).
- ``ST_Within`` / ``&&``      → polygon / administrative-area / bbox containment.
"""

from __future__ import annotations

from typing import Any

from geoalchemy2 import Geography
from sqlalchemy import Float, cast, func
from sqlalchemy.sql.elements import ColumnElement

from app.models.geo import AdministrativeArea
from app.models.mixins import SRID
from app.models.resource import Resource


def point_expr(latitude: float, longitude: float) -> Any:
    """SRID-4326 point from lat/lon."""
    return func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), SRID)


def distance_meters_column(latitude: float, longitude: float) -> ColumnElement[float]:
    """Labelled great-circle distance (metres) from the resource to the point."""
    return cast(
        func.ST_Distance(
            cast(Resource.geom, Geography),
            cast(point_expr(latitude, longitude), Geography),
        ),
        Float,
    ).label("distance_meters")


def within_radius(
    latitude: float, longitude: float, radius_m: float
) -> ColumnElement[bool]:
    """Indexed metric radius predicate."""
    return func.ST_DWithin(
        cast(Resource.geom, Geography),
        cast(point_expr(latitude, longitude), Geography),
        radius_m,
    )


def knn_order(latitude: float, longitude: float) -> ColumnElement[Any]:
    """KNN ordering expression (nearest first), index-assisted."""
    return Resource.geom.op("<->")(point_expr(latitude, longitude))


def within_polygon(polygon_wkt: str) -> ColumnElement[bool]:
    polygon = func.ST_SetSRID(func.ST_GeomFromText(polygon_wkt), SRID)
    return func.ST_Within(Resource.geom, polygon)


def within_bbox(
    min_lon: float, min_lat: float, max_lon: float, max_lat: float
) -> ColumnElement[bool]:
    envelope = func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, SRID)
    # `&&` uses the GiST index; ST_Within refines to true containment.
    return Resource.geom.op("&&")(envelope) & func.ST_Within(Resource.geom, envelope)


def within_administrative_area(area_id: Any) -> ColumnElement[bool]:
    from sqlalchemy import select

    boundary = (
        select(AdministrativeArea.boundary)
        .where(AdministrativeArea.id == area_id)
        .scalar_subquery()
    )
    return func.ST_Within(Resource.geom, boundary)
