"""Dependency wiring for the mobile API (Stage 19).

Database-free: the mobile BFF depends on no SQLAlchemy session (the default
data provider is in-memory; production swaps in a real-service adapter), so it
cannot read or write the production database directly. A single process-wide
:class:`MobilePlatform` holds all BFF state.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.mobile.services.facade import MobilePlatform

_platform: MobilePlatform | None = None


def get_mobile_platform() -> MobilePlatform:
    global _platform
    if _platform is None:
        _platform = MobilePlatform()
    return _platform


def reset_mobile_platform(platform: MobilePlatform | None = None) -> None:
    """Replace the singleton (used by tests for isolation)."""
    global _platform
    _platform = platform


MobilePlatformDep = Annotated[MobilePlatform, Depends(get_mobile_platform)]
