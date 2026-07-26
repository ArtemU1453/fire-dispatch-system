"""Enumerations for the AI-platform audit model.

Value-labels are lowercase to match the project-wide value-based enum
serialization; the native PostgreSQL types are created explicitly in the AI
migration.
"""

from __future__ import annotations

from enum import Enum


class AIAuditCapability(str, Enum):
    """Which AI capability an audit entry refers to."""

    TRANSCRIBE = "transcribe"
    EXTRACT_ENTITIES = "extract_entities"
    CLASSIFY_INCIDENT = "classify_incident"
    SUMMARIZE = "summarize"
    ANALYZE = "analyze"


class AIAuditStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
