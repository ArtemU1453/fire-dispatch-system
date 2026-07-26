"""Shared PostgreSQL enum type objects for the AI module.

Follows the project convention: one ``ENUM`` per type name, ``values_callable``
(lowercase value-labels) and ``create_type=False`` — the new types are created and
dropped exactly once by the AI migration.
"""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy.dialects.postgresql import ENUM

from app.ai.models.enums import AIAuditCapability, AIAuditStatus


def _values(enum_cls: Iterable) -> list[str]:
    return [member.value for member in enum_cls]


def _enum(py_enum, name: str) -> ENUM:
    return ENUM(py_enum, name=name, create_type=False, values_callable=_values)


ai_audit_capability_enum = _enum(AIAuditCapability, "ai_audit_capability")
ai_audit_status_enum = _enum(AIAuditStatus, "ai_audit_status")

NEW_ENUMS = (ai_audit_capability_enum, ai_audit_status_enum)

__all__ = [
    "NEW_ENUMS",
    "ai_audit_capability_enum",
    "ai_audit_status_enum",
]
