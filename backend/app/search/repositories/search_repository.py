"""SearchRepository — executes a built search query.

The single place that touches the session for search. It runs the page query and
the count query (two round trips total, regardless of result size) and normalizes
rows into ``ScoredResource`` candidates. Eager-loading options are already baked
into the page statement by the engine, so no lazy loads happen while building the
response (no N+1).
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.search.algorithms.selection import ScoredResource
from app.search.engine import BuiltQuery


class SearchResult:
    """A page of scored candidates plus the total match count."""

    __slots__ = ("candidates", "total")

    def __init__(self, candidates: list[ScoredResource], total: int) -> None:
        self.candidates = candidates
        self.total = total


class SearchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, built: BuiltQuery) -> SearchResult:
        result = await self._session.execute(built.page)
        candidates: list[ScoredResource] = []
        if built.has_distance:
            for resource, distance in result.all():
                candidates.append(
                    ScoredResource(
                        resource=resource,
                        distance_meters=(
                            float(distance) if distance is not None else None
                        ),
                    )
                )
        else:
            for resource in result.scalars().all():
                candidates.append(ScoredResource(resource=resource))

        total = int((await self._session.execute(built.count)).scalar_one())
        return SearchResult(candidates=candidates, total=total)
