"""Fixtures for the Digital Twin tests (database-free)."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.digital_twin.api.deps import reset_digital_twin_service
from app.digital_twin.planning.service import DigitalTwinService
from app.main import create_app


@pytest.fixture
def service() -> DigitalTwinService:
    svc = DigitalTwinService()
    reset_digital_twin_service(svc)
    return svc


@pytest_asyncio.fixture
async def client(service: DigitalTwinService) -> AsyncGenerator[AsyncClient]:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    reset_digital_twin_service(None)
