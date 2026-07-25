"""Pluggable selection strategies for composing the primary set."""

from __future__ import annotations

from app.dispatch.strategies.selection import (
    GreedyCapabilitySelectionStrategy,
    SelectionStrategy,
)

__all__ = ["GreedyCapabilitySelectionStrategy", "SelectionStrategy"]
