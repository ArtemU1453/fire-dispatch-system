"""Dependency wiring for the Digital Twin API (Stage 18 §9).

Like the training platform, the digital twin is **database-free**: it depends on
no SQLAlchemy session, so it cannot read or write the production database. A
single process-wide :class:`DigitalTwinService` holds the baseline model,
scenario store and results registry.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.digital_twin.planning.service import DigitalTwinService

_service: DigitalTwinService | None = None


def get_digital_twin_service() -> DigitalTwinService:
    global _service
    if _service is None:
        _service = DigitalTwinService()
    return _service


def reset_digital_twin_service(service: DigitalTwinService | None = None) -> None:
    """Replace the singleton (used by tests for isolation)."""
    global _service
    _service = service


DigitalTwinServiceDep = Annotated[
    DigitalTwinService, Depends(get_digital_twin_service)
]
