"""SearchEngine — composes criteria into a single SQL statement.

The engine is the universal core: it works over the ``Resource`` entity and knows
nothing about resource *kinds* — those are just filters. It builds one paged,
sorted, optionally distance-annotated ``SELECT`` plus a matching ``COUNT``,
applying eager loading so building the response never triggers N+1 queries.

It performs **no** ranking/selection — that is delegated to a
``SelectionStrategy`` (see ``algorithms/selection.py``) applied downstream, so a
future automatic-selection algorithm plugs in without changing the engine.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Select, func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.models.catalog import AvailabilityStatus, ResourceType
from app.models.organization import Organization
from app.models.resource import Resource
from app.search.algorithms import spatial
from app.search.criteria import (
    SearchCriteria,
    SortDirection,
    SortField,
    SpatialConstraint,
)


@dataclass(slots=True)
class BuiltQuery:
    """A page query (rows of Resource[, distance]) and its total-count query."""

    page: Select
    count: Select
    has_distance: bool


class SearchEngine:
    """Builds resource-search statements from :class:`SearchCriteria`."""

    def build(self, criteria: SearchCriteria) -> BuiltQuery:
        point = criteria.reference_point

        # --- page query --------------------------------------------------
        if point is not None:
            distance_col = spatial.distance_meters_column(
                point.latitude, point.longitude
            )
            page: Select = select(Resource, distance_col)
        else:
            distance_col = None
            page = select(Resource)

        page = self._narrow(page, criteria)
        page = self._apply_sort(page, criteria, distance_col)
        page = page.limit(criteria.pagination.limit).offset(criteria.pagination.offset)
        page = page.options(*self._eager_options())

        # --- count query (no sort/pagination/eager) ----------------------
        count = select(func.count()).select_from(
            self._narrow(select(Resource.id), criteria).subquery()
        )

        return BuiltQuery(page=page, count=count, has_distance=point is not None)

    # ------------------------------------------------------------ narrowing
    def _narrow(self, stmt: Select, criteria: SearchCriteria) -> Select:
        stmt = stmt.where(Resource.is_deleted.is_(False))
        for flt in criteria.filters:
            stmt = flt.apply(stmt)
        return self._apply_spatial(stmt, criteria.spatial)

    @staticmethod
    def _apply_spatial(stmt: Select, sp: SpatialConstraint) -> Select:
        if sp.point is not None and sp.radius_meters is not None:
            stmt = stmt.where(
                spatial.within_radius(
                    sp.point.latitude, sp.point.longitude, sp.radius_meters
                )
            )
        if sp.polygon_wkt:
            stmt = stmt.where(spatial.within_polygon(sp.polygon_wkt))
        if sp.area_id is not None:
            stmt = stmt.where(spatial.within_administrative_area(sp.area_id))
        if sp.bbox is not None:
            stmt = stmt.where(spatial.within_bbox(*sp.bbox))
        return stmt

    # -------------------------------------------------------------- sorting
    def _apply_sort(
        self,
        stmt: Select,
        criteria: SearchCriteria,
        distance_col: ColumnElement | None,
    ) -> Select:
        specs = list(criteria.sort)
        point = criteria.reference_point

        # Default: nearest-first when a reference point is given.
        if not specs and point is not None:
            return stmt.order_by(spatial.knn_order(point.latitude, point.longitude))

        join_models = {
            SortField.ORGANIZATION: Organization,
            SortField.TYPE: ResourceType,
            SortField.STATUS: AvailabilityStatus,
            SortField.PRIORITY: AvailabilityStatus,
            SortField.READINESS: AvailabilityStatus,
        }
        joined: set = set()
        order_by: list = []
        for spec in specs:
            model = join_models.get(spec.field)
            if model is not None and model not in joined:
                stmt = stmt.outerjoin(model, self._join_condition(model))
                joined.add(model)
            columns = self._sort_columns(spec.field, point)
            desc = spec.direction is SortDirection.DESC
            for col in columns:
                order_by.append(col.desc() if desc else col.asc())
        if order_by:
            stmt = stmt.order_by(*order_by)
        return stmt

    @staticmethod
    def _join_condition(model: type) -> ColumnElement[bool]:
        if model is Organization:
            return Organization.id == Resource.organization_id
        if model is ResourceType:
            return ResourceType.id == Resource.resource_type_id
        if model is AvailabilityStatus:
            return AvailabilityStatus.id == Resource.availability_status_id
        raise ValueError(f"No join condition for {model!r}")

    @staticmethod
    def _sort_columns(field: SortField, point) -> list[ColumnElement]:
        if field is SortField.DISTANCE:
            if point is None:
                return []
            return [spatial.knn_order(point.latitude, point.longitude)]
        if field is SortField.NAME:
            return [Resource.name]
        if field is SortField.ORGANIZATION:
            return [Organization.name]
        if field is SortField.TYPE:
            return [ResourceType.name]
        if field is SortField.STATUS or field is SortField.PRIORITY:
            return [AvailabilityStatus.sort_order]
        if field is SortField.READINESS:
            return [
                AvailabilityStatus.is_available_for_dispatch,
                AvailabilityStatus.sort_order,
            ]
        return []

    # --------------------------------------------------------- eager loading
    @staticmethod
    def _eager_options() -> list:
        """selectinload the commonly-rendered relationships (no N+1)."""
        return [
            selectinload(Resource.resource_type),
            selectinload(Resource.organization),
            selectinload(Resource.availability_status),
            selectinload(Resource.location),
            selectinload(Resource.vehicle),
            selectinload(Resource.station),
            selectinload(Resource.personnel),
            selectinload(Resource.equipment),
        ]
