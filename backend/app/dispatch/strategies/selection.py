"""Selection strategies — how the primary composition is chosen.

A strategy receives the consolidated requirements and the eligible candidates
(already ranked best-first) and returns the primary set. Keeping this behind a
:class:`SelectionStrategy` interface lets the composition policy evolve (or be
swapped in tests / future stages) without touching the engine.

The default :class:`GreedyCapabilitySelectionStrategy`:

1. takes the top-ranked candidates up to the recommended unit count, then
2. tops up with any candidate that still covers an unmet **mandatory** capability.

It never selects concrete units by name — only by rank and capability coverage.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from app.dispatch.algorithms.candidate import DispatchCandidate
from app.dispatch.requirements import RequirementSet


class SelectionStrategy(Protocol):
    """Chooses the primary composition from ranked, eligible candidates."""

    def select(
        self, requirements: RequirementSet, candidates: Sequence[DispatchCandidate]
    ) -> list[DispatchCandidate]: ...


class GreedyCapabilitySelectionStrategy:
    """Greedy, capability-aware selection (see module docstring)."""

    def select(
        self, requirements: RequirementSet, candidates: Sequence[DispatchCandidate]
    ) -> list[DispatchCandidate]:
        target = self._target(requirements, len(candidates))
        selected = list(candidates[:target])
        selected_ids = {c.id for c in selected}

        mandatory = [
            need for need in requirements.capabilities.values() if need.mandatory
        ]
        if not mandatory:
            return selected

        provided = self._provided(mandatory, selected)
        for candidate in candidates:
            if candidate.id in selected_ids:
                continue
            covers = [
                need.code
                for need in mandatory
                if provided.get(need.code, 0) < need.min_quantity
                and candidate.provides(need.code)
            ]
            if covers:
                selected.append(candidate)
                selected_ids.add(candidate.id)
                for code, qty in candidate.capabilities.items():
                    provided[code] = provided.get(code, 0) + qty
        return selected

    @staticmethod
    def _target(requirements: RequirementSet, available: int) -> int:
        target = requirements.recommended_units or requirements.minimum_units
        if target <= 0:
            # No explicit count — fall back to the number of mandatory
            # capabilities (at least one unit if anything is required).
            target = len(requirements.mandatory_capabilities) or (
                1 if requirements.has_requirements else 0
            )
        return min(target, available)

    @staticmethod
    def _provided(mandatory, units: Sequence[DispatchCandidate]) -> dict[str, int]:
        provided: dict[str, int] = {}
        for need in mandatory:
            provided[need.code] = sum(u.capabilities.get(need.code, 0) for u in units)
        return provided
