"""Incident management — the central entity of the system.

Every subsystem (GIS, Search, Rules, Dispatch, Routing, Recommendation) relates
to an incident. This module owns the incident lifecycle (a state machine), the
timeline, the change history and the links to recommendations and dispatched
units.
"""
