"""ResourceSelector — chooses the primary composition via a strategy.

Thin coordinator around a :class:`SelectionStrategy`: it keeps the engine
decoupled from the concrete composition policy and makes the strategy swappable.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.dispatch.algorithms.candidate import DispatchCandidate
from app.dispatch.requirements import RequirementSet
from app.dispatch.strategies import (
    GreedyCapabilitySelectionStrategy,
    SelectionStrategy,
)


class ResourceSelector:
    """Selects the primary set of units to satisfy the requirements."""

    def __init__(self, strategy: SelectionStrategy | None = None) -> None:
        self._strategy = strategy or GreedyCapabilitySelectionStrategy()

    def select_primary(
        self, requirements: RequirementSet, candidates: Sequence[DispatchCandidate]
    ) -> list[DispatchCandidate]:
        return self._strategy.select(requirements, list(candidates))
