"""Enumerations shared across the domain model.

Only genuinely *closed*, code-level sets live here as Python enums. Open,
data-driven classifications (resource types, vehicle types, roles, statuses,
capabilities, incident types) are modelled as **catalog tables** so they can be
extended without code or schema changes.
"""

from __future__ import annotations

import enum


class ResourceCategory(str, enum.Enum):
    """High-level family a :class:`ResourceType` belongs to.

    Determines which optional specialization table (if any) a resource uses.
    Adding a new *type* of resource does not require a new category — most new
    types (hydrant, water source, hospital, police, gas service, power grid,
    warehouse, command post, …) are plain resources under ``FACILITY`` /
    ``INFRASTRUCTURE`` and need only a new ``ResourceType`` row.
    """

    STATION = "station"            # fire stations / depots (Station detail)
    VEHICLE = "vehicle"            # apparatus (Vehicle detail)
    PERSONNEL = "personnel"        # people / crews (Personnel detail)
    EQUIPMENT = "equipment"        # gear / tools (Equipment detail)
    INFRASTRUCTURE = "infrastructure"  # hydrants, water sources, power grid…
    FACILITY = "facility"          # hospitals, police, warehouses, command posts…


class AuditAction(str, enum.Enum):
    """Type of change captured by an :class:`AuditLog` entry."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    DISPATCH = "dispatch"
    STATUS_CHANGE = "status_change"
