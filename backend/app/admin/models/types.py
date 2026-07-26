"""Shared PostgreSQL enum type objects for the admin module.

Follows the project convention: one ``ENUM`` per type name, ``values_callable``
(lowercase value-labels) and ``create_type=False`` — the new types are created and
dropped exactly once by the admin migration.
"""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy.dialects.postgresql import ENUM

from app.admin.models.enums import (
    AuthMethodKind,
    HealthStatus,
    IntegrationStatus,
    SettingCategory,
    SettingType,
)


def _values(enum_cls: Iterable) -> list[str]:
    return [member.value for member in enum_cls]


def _enum(py_enum, name: str) -> ENUM:
    return ENUM(py_enum, name=name, create_type=False, values_callable=_values)


setting_type_enum = _enum(SettingType, "admin_setting_type")
setting_category_enum = _enum(SettingCategory, "admin_setting_category")
integration_status_enum = _enum(IntegrationStatus, "admin_integration_status")
health_status_enum = _enum(HealthStatus, "admin_health_status")
auth_method_kind_enum = _enum(AuthMethodKind, "admin_auth_method_kind")

NEW_ENUMS = (
    setting_type_enum,
    setting_category_enum,
    integration_status_enum,
    health_status_enum,
    auth_method_kind_enum,
)

__all__ = [
    "NEW_ENUMS",
    "auth_method_kind_enum",
    "health_status_enum",
    "integration_status_enum",
    "setting_category_enum",
    "setting_type_enum",
]
