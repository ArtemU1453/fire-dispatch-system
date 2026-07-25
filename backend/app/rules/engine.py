"""RuleEngine — finds, loads, checks and returns applicable rules.

Algorithms pass an :class:`EvaluationContext` and receive ready-made rules with
their active versions. The engine:

1. **finds** candidate rules (by incident type, or all enabled),
2. **loads** each rule's active (published) version,
3. **checks** the incident-complexity link and evaluates the version's
   conditions (applicability),
4. **returns** the applicable rules, ordered by priority.

It makes no dispatch decisions and selects no concrete resources.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.rules.executors import EvaluationContext, RuleEvaluator
from app.rules.models import RulePriority
from app.rules.models.entities import Rule, RuleVersion
from app.rules.repositories import RuleRepository, active_version

_PRIORITY_RANK = {
    RulePriority.CRITICAL: 3,
    RulePriority.HIGH: 2,
    RulePriority.NORMAL: 1,
    RulePriority.LOW: 0,
}


@dataclass(slots=True)
class ApplicableRule:
    """A rule that applies to the context, paired with its active version."""

    rule: Rule
    version: RuleVersion


class RuleEngine:
    """Evaluates rule applicability for an incident context."""

    def __init__(
        self, repository: RuleRepository, evaluator: RuleEvaluator | None = None
    ) -> None:
        self._repo = repository
        self._evaluator = evaluator or RuleEvaluator()

    async def find_applicable(
        self, context: EvaluationContext
    ) -> list[ApplicableRule]:
        if context.incident_type_id is not None:
            rules = await self._repo.by_incident_type(context.incident_type_id)
        else:
            rules = await self._repo.list_full(enabled_only=True, limit=1000)

        applicable: list[ApplicableRule] = []
        for rule in rules:
            if not rule.is_enabled:
                continue
            version = active_version(rule)
            if version is None:
                continue
            if not self._complexity_matches(rule, context):
                continue
            if self._evaluator.is_applicable(version, context):
                applicable.append(ApplicableRule(rule=rule, version=version))

        applicable.sort(
            key=lambda a: _PRIORITY_RANK.get(a.version.priority, 0), reverse=True
        )
        return applicable

    async def get_active(self, rule_id) -> ApplicableRule | None:
        rule = await self._repo.get_full(rule_id)
        if rule is None:
            return None
        version = active_version(rule)
        return ApplicableRule(rule=rule, version=version) if version else None

    @staticmethod
    def _complexity_matches(rule: Rule, context: EvaluationContext) -> bool:
        """If a rule is scoped to complexity categories, the context must match."""
        categories = [c for c in rule.incident_categories if not c.is_deleted]
        if not categories:
            return True
        if context.complexity is None:
            return False
        return any(c.complexity.value == context.complexity for c in categories)
