"""Filter abstraction for resource search.

A ``ResourceFilter`` contributes a narrowing to the search ``SELECT``. Filters are
**fully composable** — the engine applies every filter in turn and they AND
together. Each filter is self-contained (adds its own predicate, using correlated
``EXISTS`` sub-queries for one-to-many / specialization tables so the main query
never multiplies rows — no ``DISTINCT`` needed, no N+1).

An "empty" filter (no values) is a no-op, so building a filter set from optional
request fields stays trivial.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from sqlalchemy import Select


class ResourceFilter(ABC):
    """A composable narrowing applied to the resource search query."""

    @abstractmethod
    def apply(self, stmt: Select) -> Select:
        """Return ``stmt`` narrowed by this filter (or unchanged if empty)."""
        raise NotImplementedError

    def is_active(self) -> bool:
        """Whether this filter actually narrows anything (has values)."""
        return True
