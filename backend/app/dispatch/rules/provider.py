"""Rule providers — where the rule set comes from.

``RuleProvider`` is the seam between the engine and rule storage. The shipped
``FileRuleProvider`` reads a YAML file; a database- or admin-API-backed provider
can be added later without changing the engine (Open/Closed).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import yaml

from app.dispatch.rules.models import DispatchRules

DEFAULT_RULES_PATH = Path(__file__).with_name("default_rules.yaml")


class RuleProvider(ABC):
    """Supplies a validated :class:`DispatchRules` set."""

    @abstractmethod
    def load(self) -> DispatchRules:
        """Load and validate the current rule set."""
        raise NotImplementedError


class FileRuleProvider(RuleProvider):
    """Loads rules from a YAML file (default: bundled ``default_rules.yaml``)."""

    def __init__(self, path: str | Path | None = None) -> None:
        self._path = Path(path) if path else DEFAULT_RULES_PATH

    def load(self) -> DispatchRules:
        with self._path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        return DispatchRules.model_validate(data)


class InMemoryRuleProvider(RuleProvider):
    """Serves a pre-built rule set (useful for tests)."""

    def __init__(self, rules: DispatchRules) -> None:
        self._rules = rules

    def load(self) -> DispatchRules:
        return self._rules
