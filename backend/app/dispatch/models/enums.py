"""Enumerations for persisted dispatch recommendations.

Value-labels are lowercase to match the project-wide value-based enum
serialization; the native PostgreSQL types are created explicitly in the
dispatch migration.
"""

from __future__ import annotations

from enum import Enum


class RecommendationRole(str, Enum):
    """The role a recommended unit plays in the composition."""

    PRIMARY = "primary"
    RESERVE = "reserve"


class ConfidenceLevel(str, Enum):
    """Qualitative confidence in a recommendation."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DispatchStatus(str, Enum):
    """Outcome of a recommendation run (advisory — nothing is dispatched)."""

    RECOMMENDED = "recommended"       # a sufficient composition was formed
    PARTIAL = "partial"               # units found, but requirements not fully met
    NO_RESOURCES = "no_resources"     # no available candidates at all


class ExclusionReason(str, Enum):
    """Why a considered resource was excluded from the composition."""

    UNAVAILABLE_STATUS = "unavailable_status"
    NOT_OPERATIONAL = "not_operational"
    NOT_DEPLOYABLE = "not_deployable"
    OUT_OF_SERVICE_ZONE = "out_of_service_zone"
    MISSING_CAPABILITY = "missing_capability"
    ORGANIZATION_CONSTRAINT = "organization_constraint"
    MANUAL_EXCLUSION = "manual_exclusion"
    NOT_SELECTED = "not_selected"     # eligible but not needed for the composition
