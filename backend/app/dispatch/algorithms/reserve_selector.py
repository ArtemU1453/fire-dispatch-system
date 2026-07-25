"""ReserveSelector — picks reserve units from the remaining candidates.

Reserves are the next-best eligible units not already in the primary set, up to
the reserve count the rules ask for. Reserves are advisory stand-bys — nothing is
dispatched.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.dispatch.algorithms.candidate import DispatchCandidate
from app.dispatch.requirements import RequirementSet


class ReserveSelector:
    """Selects reserve units after the primary composition is chosen."""

    def select_reserve(
        self,
        requirements: RequirementSet,
        ranked_candidates: Sequence[DispatchCandidate],
        primary_ids: set,
    ) -> list[DispatchCandidate]:
        target = requirements.reserve_units
        if target <= 0:
            return []
        spare = [c for c in ranked_candidates if c.id not in primary_ids]
        return spare[:target]
