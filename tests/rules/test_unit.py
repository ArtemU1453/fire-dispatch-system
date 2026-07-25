"""Unit tests for the Rule Engine internals (no database).

Covers condition evaluation (every operator), version applicability (logical
AND over conditions) and the publish-time validator.
"""

from __future__ import annotations

from app.models.enums import ResourceCategory
from app.rules.executors import (
    ConditionExecutor,
    EvaluationContext,
    RuleEvaluator,
)
from app.rules.models.entities import (
    CapabilityRequirement,
    ResourceRequirement,
    RuleAction,
    RuleCondition,
    RuleVersion,
)
from app.rules.models.enums import (
    ActionType,
    ConditionOperator,
    ConditionType,
    RulePriority,
    RuleStatus,
)
from app.rules.validators import RuleValidator


def _cond(ctype, op, value=None, field=None) -> RuleCondition:
    return RuleCondition(
        condition_type=ctype, operator=op, field=field, value=value, is_deleted=False
    )


# ---------------------------------------------------------------- executor ---
def test_eq_operator_matches_scalar() -> None:
    ex = ConditionExecutor()
    cond = _cond(ConditionType.OBJECT_TYPE, ConditionOperator.EQ, {"value": "school"})
    assert ex.evaluate(cond, EvaluationContext(object_type="school")) is True
    assert ex.evaluate(cond, EvaluationContext(object_type="hospital")) is False


def test_in_and_not_in_operators() -> None:
    ex = ConditionExecutor()
    in_cond = _cond(
        ConditionType.INCIDENT_TYPE, ConditionOperator.IN, {"values": ["fire", "dtp"]}
    )
    assert ex.evaluate(in_cond, EvaluationContext(incident_type_code="fire")) is True
    assert ex.evaluate(in_cond, EvaluationContext(incident_type_code="chem")) is False

    not_in = _cond(
        ConditionType.INCIDENT_TYPE, ConditionOperator.NOT_IN, {"values": ["chem"]}
    )
    assert ex.evaluate(not_in, EvaluationContext(incident_type_code="fire")) is True


def test_numeric_operators() -> None:
    ex = ConditionExecutor()
    gte = _cond(ConditionType.TIME_OF_DAY, ConditionOperator.GTE, {"value": 22})
    assert ex.evaluate(gte, EvaluationContext(time_of_day_hour=23)) is True
    assert ex.evaluate(gte, EvaluationContext(time_of_day_hour=8)) is False

    between = _cond(
        ConditionType.TIME_OF_DAY, ConditionOperator.BETWEEN, {"min": 22, "max": 6}
    )
    # 22..6 is a nonsense range numerically; verifies pure numeric comparison.
    assert ex.evaluate(between, EvaluationContext(time_of_day_hour=4)) is False


def test_exists_and_missing_fact() -> None:
    ex = ConditionExecutor()
    exists = _cond(ConditionType.OBJECT_TYPE, ConditionOperator.EXISTS)
    assert ex.evaluate(exists, EvaluationContext(object_type="school")) is True
    assert ex.evaluate(exists, EvaluationContext()) is False

    # A non-EXISTS operator against a missing fact never matches.
    eq = _cond(ConditionType.OBJECT_TYPE, ConditionOperator.EQ, {"value": "school"})
    assert ex.evaluate(eq, EvaluationContext()) is False


def test_contains_operator_over_capabilities() -> None:
    ex = ConditionExecutor()
    cond = _cond(
        ConditionType.CAPABILITY, ConditionOperator.CONTAINS, {"value": "water_supply"}
    )
    ctx = EvaluationContext(available_capabilities={"water_supply", "fire_suppression"})
    assert ex.evaluate(cond, ctx) is True
    no_water = EvaluationContext(available_capabilities={"foam"})
    assert ex.evaluate(cond, no_water) is False


# --------------------------------------------------------------- evaluator ---
def test_all_conditions_must_pass() -> None:
    ev = RuleEvaluator()
    version = RuleVersion(
        conditions=[
            _cond(
                ConditionType.INCIDENT_TYPE,
                ConditionOperator.IN,
                {"values": ["fire"]},
            ),
            _cond(ConditionType.TIME_OF_DAY, ConditionOperator.GTE, {"value": 20}),
        ]
    )
    assert ev.is_applicable(
        version, EvaluationContext(incident_type_code="fire", time_of_day_hour=23)
    )
    assert not ev.is_applicable(
        version, EvaluationContext(incident_type_code="fire", time_of_day_hour=10)
    )


def test_version_without_conditions_is_always_applicable() -> None:
    ev = RuleEvaluator()
    assert ev.is_applicable(RuleVersion(conditions=[]), EvaluationContext())


# --------------------------------------------------------------- validator ---
def _publishable_version() -> RuleVersion:
    return RuleVersion(
        status=RuleStatus.DRAFT,
        priority=RulePriority.HIGH,
        conditions=[],
        actions=[
            RuleAction(action_type=ActionType.REQUIRE_RESOURCES, is_deleted=False)
        ],
        resource_requirements=[
            ResourceRequirement(
                resource_category=ResourceCategory.VEHICLE,
                min_count=1,
                recommended_count=2,
                reserve_count=0,
                is_deleted=False,
            )
        ],
        capability_requirements=[],
    )


def test_validator_accepts_wellformed_version() -> None:
    assert RuleValidator().validate_for_publish(_publishable_version()) == []


def test_validator_requires_requirement_or_action() -> None:
    empty = RuleVersion(
        conditions=[], actions=[], resource_requirements=[], capability_requirements=[]
    )
    errors = RuleValidator().validate_for_publish(empty)
    assert any("at least one requirement or action" in e for e in errors)


def test_validator_rejects_incomplete_condition() -> None:
    version = _publishable_version()
    version.conditions = [
        _cond(ConditionType.INCIDENT_TYPE, ConditionOperator.IN, {})
    ]
    errors = RuleValidator().validate_for_publish(version)
    assert any("requires 'values'" in e for e in errors)


def test_validator_flags_min_over_recommended() -> None:
    version = _publishable_version()
    version.resource_requirements = [
        ResourceRequirement(
            resource_category=ResourceCategory.VEHICLE,
            min_count=5,
            recommended_count=2,
            reserve_count=0,
            is_deleted=False,
        )
    ]
    errors = RuleValidator().validate_for_publish(version)
    assert any("min_count exceeds recommended_count" in e for e in errors)


def test_validator_flags_duplicate_capability_codes() -> None:
    version = _publishable_version()
    version.capability_requirements = [
        CapabilityRequirement(capability_code="x", min_quantity=1, mandatory=True),
        CapabilityRequirement(capability_code="x", min_quantity=1, mandatory=True),
    ]
    errors = RuleValidator().validate_for_publish(version)
    assert any("Duplicate capability" in e for e in errors)
