"""Enumerations for the rules infrastructure.

These are closed, code-level sets used as native PostgreSQL enums. Open,
data-driven classifications (rule categories, tags, incident types) are tables
so new values are added as data — no code change.
"""

from __future__ import annotations

import enum


class RuleStatus(str, enum.Enum):
    """Lifecycle status of a rule *version*."""

    DRAFT = "draft"            # editable
    PUBLISHED = "published"    # immutable, can be the active version
    ARCHIVED = "archived"      # superseded, kept for history
    DEPRECATED = "deprecated"  # no longer to be used


class RulePriority(str, enum.Enum):
    """Priority of a rule / a resource requirement."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentComplexity(str, enum.Enum):
    """Incident complexity categories (категория сложности)."""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    CRITICAL = "critical"


class ConditionType(str, enum.Enum):
    """What a rule condition is evaluated against."""

    INCIDENT_TYPE = "incident_type"
    INCIDENT_COMPLEXITY = "incident_complexity"
    TIME_OF_DAY = "time_of_day"
    ADMINISTRATIVE_AREA = "administrative_area"
    OBJECT_TYPE = "object_type"
    PRIORITY = "priority"
    RESOURCE_AVAILABILITY = "resource_availability"
    CAPABILITY = "capability"


class ConditionOperator(str, enum.Enum):
    """How a condition value is compared to the context value."""

    EQ = "eq"
    NEQ = "neq"
    IN = "in"
    NOT_IN = "not_in"
    GTE = "gte"
    LTE = "lte"
    BETWEEN = "between"
    EXISTS = "exists"
    CONTAINS = "contains"


class ActionType(str, enum.Enum):
    """The kind of prescription a rule action expresses."""

    REQUIRE_RESOURCES = "require_resources"
    REQUIRE_CAPABILITY = "require_capability"
    SET_PRIORITY = "set_priority"
    SET_RESERVE = "set_reserve"
    ESCALATE = "escalate"
    NOTIFY = "notify"
    CUSTOM = "custom"


class RuleHistoryAction(str, enum.Enum):
    """A recorded change in a rule's lifecycle."""

    CREATED = "created"
    UPDATED = "updated"
    VERSION_CREATED = "version_created"
    PUBLISHED = "published"
    ACTIVATED = "activated"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"
    DELETED = "deleted"
