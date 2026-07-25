"""Dispatch selection strategy — plugs into the Stage-4 SearchEngine seam.

Implements the Stage-4 ``SelectionStrategy`` protocol so the search engine can be
asked to re-rank its candidates by dispatch score (distance + readiness) without
any change to the engine — the concrete proof of that extension point.

The full recommendation pipeline (with capability coverage and composition) runs
in the :mod:`app.dispatch.recommendations` engine, which needs data beyond what a
``ScoredResource`` carries; this strategy provides the ranking half of the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.dispatch.algorithms.scoring import Scorer
from app.dispatch.rules.models import ScoringConfig
from app.dispatch.utils.readiness import readiness_of
from app.search.algorithms.selection import ScoredResource


class DispatchSelectionStrategy:
    """Ranks search candidates by dispatch score (distance + readiness)."""

    def __init__(self, scoring: ScoringConfig) -> None:
        self._scorer = Scorer(scoring)

    def apply(self, candidates: Sequence[ScoredResource]) -> list[ScoredResource]:
        for candidate in candidates:
            score = self._scorer.score(
                distance_meters=candidate.distance_meters,
                readiness=readiness_of(candidate.resource),
                capabilities={},
            )
            candidate.score = score.total
        return sorted(candidates, key=lambda c: c.score or 0.0, reverse=True)
