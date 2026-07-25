"""Externalized dispatch rules (Rule Engine)."""

from app.dispatch.rules.engine import RuleEngine
from app.dispatch.rules.models import (
    CapabilityRequirement,
    DispatchRules,
    ExclusionConfig,
    IncidentRule,
    ScoringConfig,
)
from app.dispatch.rules.provider import (
    DEFAULT_RULES_PATH,
    FileRuleProvider,
    InMemoryRuleProvider,
    RuleProvider,
)

__all__ = [
    "RuleEngine",
    "DispatchRules",
    "IncidentRule",
    "CapabilityRequirement",
    "ScoringConfig",
    "ExclusionConfig",
    "RuleProvider",
    "FileRuleProvider",
    "InMemoryRuleProvider",
    "DEFAULT_RULES_PATH",
]
