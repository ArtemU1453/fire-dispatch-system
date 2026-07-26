"""Fixtures for the mobile BFF tests (database-free)."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.mobile.api.deps import reset_mobile_platform
from app.mobile.services.facade import MobilePlatform


@pytest.fixture
def platform() -> MobilePlatform:
    p = MobilePlatform()
    reset_mobile_platform(p)
    return p


@pytest_asyncio.fixture
async def client(platform: MobilePlatform) -> AsyncGenerator[AsyncClient]:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    reset_mobile_platform(None)
