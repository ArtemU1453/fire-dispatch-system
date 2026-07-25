"""RuleService — the single entry point algorithms use to obtain rules.

Read side: list / fetch rules, resolve rules for an incident type, list versions,
and return ready-made requirements (minimum / recommended composition, required
capabilities). Write side delegates to :class:`RuleWriteService` (versioning).
Downstream algorithms never embed a norm — they call this service.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.rules.repositories import RuleRepository, RuleVersionRepository, active_version
from app.rules.schemas.rule import (
    RuleResponse,
    RuleSummaryResponse,
    RuleVersionResponse,
)
from app.rules.schemas.service import RequirementsResponse
from app.rules.services.versioning import RuleWriteService
from app.rules.utils.mapping import (
    rule_to_response,
    rule_to_summary,
    to_requirements,
    version_to_response,
)


class RuleService:
    """Read/query facade over the rules infrastructure."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._rules = RuleRepository(session)
        self._versions = RuleVersionRepository(session)
        self._write = RuleWriteService(session)

    # ------------------------------------------------------------- reads
    async def list_rules(
        self,
        *,
        category_id: UUID | None = None,
        enabled_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RuleSummaryResponse]:
        rules = await self._rules.list_full(
            category_id=category_id, enabled_only=enabled_only,
            limit=limit, offset=offset,
        )
        return [rule_to_summary(r) for r in rules]

    async def get_rule(self, rule_id: UUID) -> RuleResponse:
        rule = await self._rules.get_full(rule_id)
        if rule is None:
            raise NotFoundError("Rule not found")
        return rule_to_response(rule)

    async def get_by_category(self, category_id: UUID) -> list[RuleSummaryResponse]:
        rules = await self._rules.list_full(category_id=category_id, limit=1000)
        return [rule_to_summary(r) for r in rules]

    async def get_by_incident_type(
        self, incident_type_id: UUID
    ) -> list[RuleResponse]:
        """Active rules linked to an incident type.

        This is a *listing*: it returns every enabled rule linked to the incident
        type that has an active published version. Full applicability (complexity,
        time-of-day, capabilities, …) is evaluated by the dispatch algorithm via
        :meth:`RuleEngine.find_applicable` with a complete incident context.
        """
        rules = await self._rules.by_incident_type(incident_type_id)
        return [
            rule_to_response(r) for r in rules if active_version(r) is not None
        ]

    async def get_active_rules(self) -> list[RuleResponse]:
        rules = await self._rules.list_full(enabled_only=True, limit=1000)
        return [rule_to_response(r) for r in rules if active_version(r) is not None]

    async def get_versions(self, rule_id: UUID) -> list[RuleVersionResponse]:
        rule = await self._rules.get(rule_id)
        if rule is None:
            raise NotFoundError("Rule not found")
        versions = await self._versions.versions_of(rule_id)
        return [version_to_response(v) for v in versions]

    async def get_requirements(self, rule_id: UUID) -> RequirementsResponse:
        rule = await self._rules.get_full(rule_id)
        if rule is None:
            raise NotFoundError("Rule not found")
        version = active_version(rule)
        if version is None:
            raise NotFoundError("Rule has no active published version")
        return to_requirements(rule, version)

    # ------------------------------------------------------------- writes
    async def create_rule(self, data) -> RuleResponse:
        rule = await self._write.create_rule(data)
        return rule_to_response(rule)

    async def update_rule(self, rule_id: UUID, data) -> RuleResponse:
        rule = await self._write.update_rule(rule_id, data)
        return rule_to_response(rule)

    async def delete_rule(self, rule_id: UUID) -> None:
        await self._write.delete_rule(rule_id)
