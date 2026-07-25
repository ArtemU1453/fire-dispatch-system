"""Shared PostgreSQL enum type objects for the dispatch module.

Mirrors the rules module convention: one ``ENUM`` object per type name with
``values_callable`` (lowercase value-labels) and ``create_type=False`` — the
new types are created/dropped exactly once by the dispatch migration.

``incident_complexity`` and ``rule_priority`` are **reused** from the rules
stage (already present in the database); they are referenced with
``create_type=False`` and never recreated here.
"""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy.dialects.postgresql import ENUM

from app.dispatch.models.enums import (
    ConfidenceLevel,
    DispatchStatus,
    ExclusionReason,
    RecommendationRole,
)
from app.rules.models.types import incident_complexity_enum, rule_priority_enum


def _values(enum_cls: Iterable) -> list[str]:
    return [member.value for member in enum_cls]


def _enum(py_enum, name: str) -> ENUM:
    return ENUM(py_enum, name=name, create_type=False, values_callable=_values)


recommendation_role_enum = _enum(RecommendationRole, "recommendation_role")
confidence_level_enum = _enum(ConfidenceLevel, "recommendation_confidence")
dispatch_status_enum = _enum(DispatchStatus, "dispatch_status")
exclusion_reason_enum = _enum(ExclusionReason, "dispatch_exclusion_reason")

# New enum types managed explicitly by the dispatch migration.
NEW_ENUMS = (
    recommendation_role_enum,
    confidence_level_enum,
    dispatch_status_enum,
    exclusion_reason_enum,
)

# Reused from the rules stage — referenced, never (re)created here.
__all__ = [
    "NEW_ENUMS",
    "confidence_level_enum",
    "dispatch_status_enum",
    "exclusion_reason_enum",
    "incident_complexity_enum",
    "recommendation_role_enum",
    "rule_priority_enum",
]
