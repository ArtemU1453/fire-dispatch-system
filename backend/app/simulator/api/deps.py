"""Dependency wiring for the simulator API (Stage 17).

The simulator is deliberately **database-free**: it depends on no SQLAlchemy
session, so it cannot read or write the production database. A single
process-wide :class:`SimulatorService` holds the in-memory sessions and the
scenario store.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.simulator.services.service import SimulatorService

_service: SimulatorService | None = None


def get_simulator_service() -> SimulatorService:
    """Return the process-wide simulator service (lazy singleton)."""
    global _service
    if _service is None:
        _service = SimulatorService()
    return _service


def reset_simulator_service(service: SimulatorService | None = None) -> None:
    """Replace the singleton (used by tests for isolation)."""
    global _service
    _service = service


SimulatorServiceDep = Annotated[SimulatorService, Depends(get_simulator_service)]
