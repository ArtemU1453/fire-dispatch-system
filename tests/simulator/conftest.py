"""Fixtures for the simulator tests.

The simulation & training platform is database-free, so these tests need no
PostgreSQL and run everywhere. Each test gets a fresh, isolated service.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.simulator.api.deps import reset_simulator_service
from app.simulator.services.service import SimulatorService


@pytest.fixture
def service() -> SimulatorService:
    svc = SimulatorService()
    reset_simulator_service(svc)
    return svc


@pytest_asyncio.fixture
async def client(service: SimulatorService) -> AsyncGenerator[AsyncClient]:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    reset_simulator_service(None)
