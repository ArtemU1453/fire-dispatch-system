"""Enumerations for the administration module.

Value-labels are lowercase to match the project-wide value-based enum
serialization; the native PostgreSQL types are created explicitly in the admin
migration. Only genuinely closed sets are enums — open classifications (account
statuses, integration providers) are catalog **tables** so they can be edited
without code changes.
"""

from __future__ import annotations

from enum import Enum


class SettingType(str, Enum):
    """The value type of a system setting (how ``value`` is parsed)."""

    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    JSON = "json"


class SettingCategory(str, Enum):
    """Configuration categories (stage §4)."""

    GENERAL = "general"
    MAPS = "maps"
    ROUTING = "routing"
    AI = "ai"
    SEARCH = "search"
    DISPATCH = "dispatch"
    LOGGING = "logging"
    NOTIFICATIONS = "notifications"
    INTEGRATIONS = "integrations"
    SECURITY = "security"


class IntegrationStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class AuthMethodKind(str, Enum):
    """Kinds of authentication method — external ones are architecture only."""

    PASSWORD = "password"
    LDAP = "ldap"
    ACTIVE_DIRECTORY = "active_directory"
    OIDC = "oidc"
    SAML = "saml"
    OTHER = "other"
