"""Position provider — the seam for obtaining unit coordinates.

Location *sources* (GPS/AVL, an external tracking service, …) plug in behind this
interface without touching the business logic. This stage implements only the
interface plus a default provider that returns the coordinates already stored on
the resource (Stage-2 ``resources.latitude/longitude``). **No GPS tracking** is
implemented here — that is a later concern.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resource import Resource


@dataclass(slots=True)
class Position:
    """A resource's position at a point in time."""

    resource_id: UUID
    latitude: float
    longitude: float
    recorded_at: datetime | None = None
    source: str = "stored"


class PositionProvider(ABC):
    """Abstract source of resource positions."""

    name: str = "base"

    @abstractmethod
    async def get_position(self, resource_id: UUID) -> Position | None:
        """The current position of one resource (or ``None`` if unknown)."""
        raise NotImplementedError

    @abstractmethod
    async def get_positions(
        self, resource_ids: Sequence[UUID]
    ) -> dict[UUID, Position]:
        """Current positions for several resources (batch)."""
        raise NotImplementedError


class StoredPositionProvider(PositionProvider):
    """Default provider: reads the coordinates stored on the resource."""

    name = "stored"

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_position(self, resource_id: UUID) -> Position | None:
        result = await self.get_positions([resource_id])
        return result.get(resource_id)

    async def get_positions(
        self, resource_ids: Sequence[UUID]
    ) -> dict[UUID, Position]:
        if not resource_ids:
            return {}
        rows = await self._session.execute(
            select(Resource.id, Resource.latitude, Resource.longitude).where(
                Resource.id.in_(list(resource_ids))
            )
        )
        out: dict[UUID, Position] = {}
        for rid, lat, lon in rows.all():
            if lat is not None and lon is not None:
                out[rid] = Position(resource_id=rid, latitude=lat, longitude=lon)
        return out
