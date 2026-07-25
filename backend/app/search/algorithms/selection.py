"""Selection-strategy seam.

The **next stage** (automatic unit selection) plugs a ranking/selection algorithm
in here *without changing the SearchEngine*. The engine and service already
produce a scored candidate list (resources + distance); a ``SelectionStrategy``
post-processes that list (re-rank, cap, weight by capability, etc.).

This stage ships only the identity strategy — it preserves the search order
(distance / requested sort). No automatic selection, weighting or ETA is done
here, per the stage constraints.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.models.resource import Resource


@dataclass(slots=True)
class ScoredResource:
    """A search candidate: the resource plus its optional distance and score."""

    resource: Resource
    distance_meters: float | None = None
    score: float | None = None

    @property
    def id(self) -> UUID:
        return self.resource.id


class SelectionStrategy(Protocol):
    """Post-processes ranked candidates. Implemented by the next stage."""

    def apply(self, candidates: Sequence[ScoredResource]) -> list[ScoredResource]: ...


class IdentitySelection:
    """Default strategy — returns candidates unchanged (no selection)."""

    def apply(self, candidates: Sequence[ScoredResource]) -> list[ScoredResource]:
        return list(candidates)
