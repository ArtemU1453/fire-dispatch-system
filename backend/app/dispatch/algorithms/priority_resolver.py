"""PriorityResolver — resolves incident priority and ranks candidates.

Incident priority comes from the applicable rules (the highest), optionally
raised by an explicit danger level on the request. Candidate ranking is by score
(best first), with distance as a stable tie-breaker.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.dispatch.algorithms.candidate import DispatchCandidate
from app.dispatch.requirements import RequirementSet
from app.rules.models.enums import RulePriority

_RANK = {
    RulePriority.LOW: 0,
    RulePriority.NORMAL: 1,
    RulePriority.HIGH: 2,
    RulePriority.CRITICAL: 3,
}
_BY_RANK = {rank: priority for priority, rank in _RANK.items()}

# Danger-level keywords that map to a minimum priority floor.
_DANGER_FLOOR = {
    "critical": RulePriority.CRITICAL,
    "high": RulePriority.HIGH,
    "elevated": RulePriority.HIGH,
    "medium": RulePriority.NORMAL,
    "low": RulePriority.LOW,
}


class PriorityResolver:
    """Resolves the effective incident priority and orders candidates."""

    def resolve(
        self, requirements: RequirementSet, danger_level: str | None = None
    ) -> RulePriority:
        priority = requirements.priority
        floor = self._danger_floor(danger_level)
        if floor is not None and _RANK[floor] > _RANK[priority]:
            return floor
        return priority

    @staticmethod
    def _danger_floor(danger_level: str | None) -> RulePriority | None:
        if not danger_level:
            return None
        return _DANGER_FLOOR.get(danger_level.strip().lower())

    @staticmethod
    def rank_candidates(
        candidates: Sequence[DispatchCandidate],
    ) -> list[DispatchCandidate]:
        return sorted(
            candidates,
            key=lambda c: (
                -c.score_value,
                c.distance_meters if c.distance_meters is not None else float("inf"),
            ),
        )
