"""Repository-level integration tests (PostgreSQL).

Exercises eager loading (no N+1), the active-version resolver and the
incident-type lookup used by the Rule Engine.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.rules.models.enums import ActionType, RulePriority
from app.rules.repositories import RuleRepository, active_version
from app.rules.schemas.content import (
    ActionInput,
    CapabilityRequirementInput,
    ResourceRequirementInput,
    VersionContentInput,
)
from app.rules.schemas.rule import RuleCreate
from app.rules.services.versioning import RuleWriteService

from .conftest import RulesSeed

pytestmark = pytest.mark.asyncio


def _create(seed: RulesSeed, code: str, *, publish: bool = True) -> RuleCreate:
    from app.models.enums import ResourceCategory

    return RuleCreate(
        code=code,
        name="Rule",
        category_id=seed.category_id,
        incident_type_ids=[seed.incident_type_id],
        complexities=["moderate"],
        tags=["fire"],
        publish=publish,
        version=VersionContentInput(
            priority=RulePriority.HIGH,
            actions=[ActionInput(action_type=ActionType.REQUIRE_RESOURCES)],
            resource_requirements=[
                ResourceRequirementInput(
                    resource_category=ResourceCategory.VEHICLE,
                    min_count=2,
                    recommended_count=3,
                )
            ],
            capability_requirements=[
                CapabilityRequirementInput(capability_code="fire_suppression")
            ],
        ),
    )


async def test_get_full_eager_loads_everything(
    pg_factory: async_sessionmaker, seed: RulesSeed
) -> None:
    code = f"{seed.prefix}-R1"
    async with pg_factory() as s:
        rule = await RuleWriteService(s).create_rule(_create(seed, code))
        await s.commit()
        rule_id = rule.id

    # Fresh session: no identity-map help — proves the query eager-loads.
    async with pg_factory() as s:
        loaded = await RuleRepository(s).get_full(rule_id)
        assert loaded is not None
        version = active_version(loaded)
        assert version is not None
        assert version.version_number == 1
        assert [r.min_count for r in version.resource_requirements] == [2]
        assert {t.tag for t in loaded.tags} == {"fire"}
        assert len(loaded.incident_types) == 1


async def test_by_incident_type_returns_enabled_rules(
    pg_factory: async_sessionmaker, seed: RulesSeed
) -> None:
    async with pg_factory() as s:
        await RuleWriteService(s).create_rule(_create(seed, f"{seed.prefix}-R2"))
        await s.commit()

    async with pg_factory() as s:
        rules = await RuleRepository(s).by_incident_type(seed.incident_type_id)
        codes = {r.code for r in rules}
        assert f"{seed.prefix}-R2" in codes


async def test_unpublished_rule_has_no_active_version(
    pg_factory: async_sessionmaker, seed: RulesSeed
) -> None:
    code = f"{seed.prefix}-R3"
    async with pg_factory() as s:
        rule = await RuleWriteService(s).create_rule(
            _create(seed, code, publish=False)
        )
        await s.commit()
        rule_id = rule.id

    async with pg_factory() as s:
        loaded = await RuleRepository(s).get_full(rule_id)
        assert loaded is not None
        assert active_version(loaded) is None
