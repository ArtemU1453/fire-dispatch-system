"""Search algorithms: spatial predicates and the selection-strategy seam."""

from app.search.algorithms.selection import (
    IdentitySelection,
    ScoredResource,
    SelectionStrategy,
)

__all__ = ["ScoredResource", "SelectionStrategy", "IdentitySelection"]
