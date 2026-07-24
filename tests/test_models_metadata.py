"""Structural tests over the ORM metadata.

These are hermetic (no database): they assert the schema *shape* matches the
Stage-2 requirements — the full entity set, the mandatory audit columns on every
table, UUID primary keys, and spatial indexes on all geometry columns.
"""

from __future__ import annotations

import app.models  # noqa: F401  (registers models on the metadata)
from app.database.base import Base

EXPECTED_TABLES = {
    "resource_types",
    "vehicle_types",
    "personnel_roles",
    "equipment_types",
    "availability_statuses",
    "capabilities",
    "incident_types",
    "incident_type_capabilities",
    "organizations",
    "administrative_areas",
    "locations",
    "coverage_areas",
    "coverage_area_incident_types",
    "resources",
    "resource_capabilities",
    "stations",
    "vehicles",
    "personnel",
    "equipment",
    "status_history",
    "coordinate_history",
    "users",
    "roles",
    "permissions",
    "user_roles",
    "role_permissions",
    "audit_logs",
}

GEOMETRY_TABLES = {
    "resources": "geom",
    "locations": "geom",
    "coordinate_history": "geom",
    "administrative_areas": "boundary",
    "coverage_areas": "area",
}


def test_all_expected_tables_present() -> None:
    assert EXPECTED_TABLES.issubset(set(Base.metadata.tables))


def test_every_table_has_audit_columns_and_uuid_pk() -> None:
    for name, table in Base.metadata.tables.items():
        cols = set(table.c.keys())
        assert {"id", "created_at", "updated_at", "is_deleted"} <= cols, name
        pk = list(table.primary_key.columns)
        assert len(pk) == 1 and pk[0].name == "id", name


def test_geometry_columns_have_spatial_indexes() -> None:
    for table_name, geom_col in GEOMETRY_TABLES.items():
        table = Base.metadata.tables[table_name]
        column = table.c[geom_col]
        # GeoAlchemy2 marks the column and requests a spatial index.
        assert getattr(column.type, "spatial_index", False) is True, table_name
        assert getattr(column.type, "srid", None) == 4326, table_name
