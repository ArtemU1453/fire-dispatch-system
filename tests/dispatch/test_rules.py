"""Unit tests for the Rule Engine (externalized rules, no DB)."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from app.core.exceptions import NotFoundError
from app.dispatch.rules import (
    DispatchRules,
    FileRuleProvider,
    InMemoryRuleProvider,
    RuleEngine,
)


def test_default_rules_load() -> None:
    engine = RuleEngine()
    assert engine.has_incident_type("fire")
    assert len(engine.incident_types()) >= 10


def test_incident_rule_fields() -> None:
    rule = RuleEngine().incident_rule("fire")
    assert rule.name == "Пожар"
    assert rule.priority == 1
    assert rule.minimum_units == 2
    assert {c.code for c in rule.required_capabilities} == {
        "fire_suppression",
        "water_supply",
    }


def test_unknown_incident_type_raises() -> None:
    with pytest.raises(NotFoundError):
        RuleEngine().incident_rule("does-not-exist")


def test_scoring_and_exclusions_exposed() -> None:
    engine = RuleEngine()
    assert engine.scoring.weights.distance > 0
    assert "maintenance" in engine.exclusions.excluded_status_codes


def test_rules_can_be_reloaded_from_file(tmp_path: Path) -> None:
    rules_file = tmp_path / "rules.yaml"
    rules_file.write_text(
        textwrap.dedent(
            """
            version: "test"
            incident_types:
              custom:
                code: custom
                name: Custom
                priority: 2
                resource_categories: [vehicle]
                minimum_units: 1
                recommended_units: 1
            """
        ),
        encoding="utf-8",
    )
    engine = RuleEngine(FileRuleProvider(rules_file))
    assert engine.has_incident_type("custom")
    assert not engine.has_incident_type("fire")  # custom file replaces defaults


def test_in_memory_provider() -> None:
    rules = DispatchRules(version="x")
    engine = RuleEngine(InMemoryRuleProvider(rules))
    assert engine.rules.version == "x"
    assert engine.incident_types() == []
