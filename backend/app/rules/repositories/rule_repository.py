"""Repositories for the rules infrastructure.

``RuleRepository`` loads a rule with its versions and each version's content
(conditions, actions, requirements) eagerly, so callers never trigger N+1. The
other entities reuse the generic Stage-2 repository.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.repositories.base import SqlAlchemyRepository
from app.rules.models import (
    IncidentTypeRule,
    Rule,
    RuleCategory,
    RuleSet,
    RuleStatus,
    RuleVersion,
)


def _rule_load_options() -> list:
    """Eager-load a rule's full content (no N+1)."""
    return [
        selectinload(Rule.category),
        selectinload(Rule.rule_set),
        selectinload(Rule.tags),
        selectinload(Rule.incident_types),
        selectinload(Rule.incident_categories),
        selectinload(Rule.versions).selectinload(RuleVersion.conditions),
        selectinload(Rule.versions).selectinload(RuleVersion.actions),
        selectinload(Rule.versions).selectinload(RuleVersion.resource_requirements),
        selectinload(Rule.versions).selectinload(RuleVersion.capability_requirements),
    ]


class RuleRepository(SqlAlchemyRepository[Rule]):
    model = Rule

    async def get_full(self, rule_id: UUID) -> Rule | None:
        stmt = (
            select(Rule)
            .where(Rule.id == rule_id, Rule.is_deleted.is_(False))
            .options(*_rule_load_options())
        )
        return (await self._session.execute(stmt)).scalars().first()

    async def get_by_code(self, code: str) -> Rule | None:
        stmt = (
            select(Rule)
            .where(Rule.code == code, Rule.is_deleted.is_(False))
            .options(*_rule_load_options())
        )
        return (await self._session.execute(stmt)).scalars().first()

    async def list_full(
        self,
        *,
        category_id: UUID | None = None,
        enabled_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Rule]:
        stmt = select(Rule).where(Rule.is_deleted.is_(False))
        if category_id is not None:
            stmt = stmt.where(Rule.category_id == category_id)
        if enabled_only:
            stmt = stmt.where(Rule.is_enabled.is_(True))
        stmt = stmt.options(*_rule_load_options()).limit(limit).offset(offset)
        return (await self._session.execute(stmt)).scalars().all()

    async def by_incident_type(self, incident_type_id: UUID) -> Sequence[Rule]:
        stmt = (
            select(Rule)
            .join(IncidentTypeRule, IncidentTypeRule.rule_id == Rule.id)
            .where(
                IncidentTypeRule.incident_type_id == incident_type_id,
                IncidentTypeRule.is_deleted.is_(False),
                Rule.is_deleted.is_(False),
                Rule.is_enabled.is_(True),
            )
            .options(*_rule_load_options())
        )
        return (await self._session.execute(stmt)).scalars().unique().all()


def active_version(rule: Rule) -> RuleVersion | None:
    """Return the rule's active, published version (if any)."""
    for version in rule.versions:
        if (
            version.is_active
            and not version.is_deleted
            and version.status == RuleStatus.PUBLISHED
        ):
            return version
    return None


class RuleVersionRepository(SqlAlchemyRepository[RuleVersion]):
    model = RuleVersion

    async def versions_of(self, rule_id: UUID) -> Sequence[RuleVersion]:
        stmt = (
            select(RuleVersion)
            .where(RuleVersion.rule_id == rule_id, RuleVersion.is_deleted.is_(False))
            .order_by(RuleVersion.version_number.desc())
            .options(
                selectinload(RuleVersion.conditions),
                selectinload(RuleVersion.actions),
                selectinload(RuleVersion.resource_requirements),
                selectinload(RuleVersion.capability_requirements),
            )
        )
        return (await self._session.execute(stmt)).scalars().all()

    async def max_version_number(self, rule_id: UUID) -> int:
        stmt = select(RuleVersion.version_number).where(
            RuleVersion.rule_id == rule_id
        )
        numbers = (await self._session.execute(stmt)).scalars().all()
        return max(numbers, default=0)


class RuleCategoryRepository(SqlAlchemyRepository[RuleCategory]):
    model = RuleCategory


class RuleSetRepository(SqlAlchemyRepository[RuleSet]):
    model = RuleSet


def make_rule_repository(session: AsyncSession) -> RuleRepository:
    return RuleRepository(session)
