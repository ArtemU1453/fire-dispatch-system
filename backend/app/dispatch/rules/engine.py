"""RuleEngine — the single access point to dispatch rules.

Loads the rule set from a :class:`RuleProvider` (cached) and exposes typed
lookups. Business logic asks the RuleEngine for an incident's rule, the scoring
config and the exclusion config — it never reads the YAML or hard-codes values.
``reload()`` re-reads the provider so rule edits apply without a restart.
"""

from __future__ import annotations

from app.core.exceptions import NotFoundError
from app.dispatch.rules.models import (
    DispatchRules,
    ExclusionConfig,
    IncidentRule,
    ScoringConfig,
)
from app.dispatch.rules.provider import FileRuleProvider, RuleProvider


class RuleEngine:
    """Provides validated dispatch rules to the rest of the module."""

    def __init__(self, provider: RuleProvider | None = None) -> None:
        self._provider = provider or FileRuleProvider()
        self._rules: DispatchRules | None = None

    @property
    def rules(self) -> DispatchRules:
        if self._rules is None:
            self._rules = self._provider.load()
        return self._rules

    def reload(self) -> DispatchRules:
        """Force a reload from the provider (rules edited without a restart)."""
        self._rules = self._provider.load()
        return self._rules

    def incident_rule(self, incident_type: str) -> IncidentRule:
        rule = self.rules.incident_types.get(incident_type)
        if rule is None:
            raise NotFoundError(f"Unknown incident type: {incident_type!r}")
        return rule

    def has_incident_type(self, incident_type: str) -> bool:
        return incident_type in self.rules.incident_types

    def incident_types(self) -> list[IncidentRule]:
        return list(self.rules.incident_types.values())

    @property
    def scoring(self) -> ScoringConfig:
        return self.rules.scoring

    @property
    def exclusions(self) -> ExclusionConfig:
        return self.rules.exclusions
