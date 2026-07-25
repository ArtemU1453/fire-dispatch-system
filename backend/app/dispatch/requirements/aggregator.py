"""Aggregate the applicable rules into one requirement set.

The Rule Engine may return several applicable rules for an incident. The
dispatch engine needs a single, consolidated statement of *what is required*:

* the union of required capabilities (strictest ``min_quantity``, mandatory wins);
* per-category minimum / recommended / reserve counts (element-wise **max**, so
  satisfying the consolidated set satisfies every contributing rule);
* the overall priority (the highest among the rules).

This module is pure: it reads the eager-loaded ORM versions and produces plain
domain objects. It selects no resources and reads no database.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from uuid import UUID

from app.dispatch.config import DispatchConfig
from app.models.enums import ResourceCategory
from app.rules.engine import ApplicableRule
from app.rules.models.enums import RulePriority

_PRIORITY_RANK = {
    RulePriority.LOW: 0,
    RulePriority.NORMAL: 1,
    RulePriority.HIGH: 2,
    RulePriority.CRITICAL: 3,
}


@dataclass(slots=True)
class CapabilityNeed:
    """A required capability, consolidated across rules."""

    code: str
    min_quantity: int
    mandatory: bool


@dataclass(slots=True)
class RequirementSet:
    """The consolidated requirements for one incident."""

    resource_categories: set[ResourceCategory] = field(default_factory=set)
    capabilities: dict[str, CapabilityNeed] = field(default_factory=dict)
    category_minimum: dict[ResourceCategory, int] = field(default_factory=dict)
    category_recommended: dict[ResourceCategory, int] = field(default_factory=dict)
    category_reserve: dict[ResourceCategory, int] = field(default_factory=dict)
    priority: RulePriority = RulePriority.NORMAL
    search_radius_meters: float = 0.0
    rule_ids: list[UUID] = field(default_factory=list)
    rule_codes: list[str] = field(default_factory=list)

    @property
    def mandatory_capabilities(self) -> list[str]:
        return sorted(c.code for c in self.capabilities.values() if c.mandatory)

    @property
    def required_capability_codes(self) -> list[str]:
        return sorted(self.capabilities)

    @property
    def minimum_units(self) -> int:
        return sum(self.category_minimum.values())

    @property
    def recommended_units(self) -> int:
        return max(sum(self.category_recommended.values()), self.minimum_units)

    @property
    def reserve_units(self) -> int:
        return sum(self.category_reserve.values())

    @property
    def has_requirements(self) -> bool:
        return bool(self.resource_categories or self.capabilities)


class RequirementAggregator:
    """Consolidates applicable rules into a :class:`RequirementSet`."""

    def __init__(self, config: DispatchConfig | None = None) -> None:
        self._config = config or DispatchConfig()

    def aggregate(self, applicable: Sequence[ApplicableRule]) -> RequirementSet:
        result = RequirementSet(
            search_radius_meters=self._config.default_search_radius_meters
        )
        best_rank = -1
        for entry in applicable:
            result.rule_ids.append(entry.rule.id)
            result.rule_codes.append(entry.rule.code)
            best_rank = max(best_rank, _PRIORITY_RANK.get(entry.version.priority, 1))

            for req in entry.version.resource_requirements:
                if req.is_deleted:
                    continue
                cat = req.resource_category
                result.resource_categories.add(cat)
                result.category_minimum[cat] = max(
                    result.category_minimum.get(cat, 0), req.min_count
                )
                result.category_recommended[cat] = max(
                    result.category_recommended.get(cat, 0), req.recommended_count
                )
                result.category_reserve[cat] = max(
                    result.category_reserve.get(cat, 0), req.reserve_count
                )

            for cap in entry.version.capability_requirements:
                if cap.is_deleted:
                    continue
                existing = result.capabilities.get(cap.capability_code)
                if existing is None:
                    result.capabilities[cap.capability_code] = CapabilityNeed(
                        code=cap.capability_code,
                        min_quantity=cap.min_quantity,
                        mandatory=cap.mandatory,
                    )
                else:
                    existing.min_quantity = max(
                        existing.min_quantity, cap.min_quantity
                    )
                    existing.mandatory = existing.mandatory or cap.mandatory

        if best_rank >= 0:
            result.priority = next(
                p for p, r in _PRIORITY_RANK.items() if r == best_rank
            )
        return result
