"""Rule write / versioning service.

Enforces the versioning rules: every change to a rule's *content* creates a new
version; published versions are immutable; only one version is active at a time;
all lifecycle events are recorded in ``rule_history``.

Rule *metadata* (name, description, enabled, links, tags) may be edited in place;
the normative *content* (conditions, actions, requirements, priority) lives in
versions.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.rules.models import (
    IncidentCategoryRule,
    IncidentTypeRule,
    Rule,
    RuleHistory,
    RuleHistoryAction,
    RuleStatus,
    RuleTag,
    RuleVersion,
)
from app.rules.models.entities import (
    CapabilityRequirement,
    ResourceRequirement,
    RuleAction,
    RuleCondition,
)
from app.rules.repositories import RuleRepository, RuleVersionRepository, active_version
from app.rules.schemas.content import VersionContentInput
from app.rules.schemas.rule import RuleCreate, RuleUpdate
from app.rules.validators import RuleValidator


class RuleWriteService:
    """Creates and updates rules under strict versioning."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._rules = RuleRepository(session)
        self._versions = RuleVersionRepository(session)
        self._validator = RuleValidator()

    async def create_rule(self, data: RuleCreate) -> Rule:
        if await self._rules.get_by_code(data.code) is not None:
            raise ConflictError(f"Rule code already exists: {data.code!r}")
        rule = Rule(
            code=data.code,
            name=data.name,
            description=data.description,
            category_id=data.category_id,
            rule_set_id=data.rule_set_id,
            is_enabled=data.is_enabled,
        )
        # Populate child collections while the rule is still *pending*: assigning
        # ``delete-orphan`` relationships on a flushed instance would lazy-load the
        # existing collection (unsupported under the async engine).
        self._apply_links(rule, data.incident_type_ids, data.complexities, data.tags)
        version = self._build_version(1, data.version)
        rule.versions.append(version)
        self._session.add(rule)
        await self._session.flush()
        self._log(rule.id, version.id, RuleHistoryAction.CREATED)
        self._log(rule.id, version.id, RuleHistoryAction.VERSION_CREATED)

        if data.publish:
            await self._publish_and_activate(rule.id, version)

        await self._session.flush()
        return await self._require_full(rule.id)

    async def update_rule(self, rule_id: UUID, data: RuleUpdate) -> Rule:
        rule = await self._rules.get_full(rule_id)
        if rule is None:
            raise NotFoundError("Rule not found")

        if data.name is not None:
            rule.name = data.name
        if data.description is not None:
            rule.description = data.description
        if data.is_enabled is not None:
            rule.is_enabled = data.is_enabled
        if data.rule_set_id is not None:
            rule.rule_set_id = data.rule_set_id
        if (
            data.incident_type_ids is not None
            or data.complexities is not None
            or data.tags is not None
        ):
            self._replace_links(rule, data)
        self._log(rule.id, None, RuleHistoryAction.UPDATED)

        if data.new_version is not None:
            number = await self._versions.max_version_number(rule_id) + 1
            version = self._build_version(number, data.new_version)
            rule.versions.append(version)
            await self._session.flush()
            self._log(rule_id, version.id, RuleHistoryAction.VERSION_CREATED)
            if data.publish:
                await self._publish_and_activate(rule_id, version)

        await self._session.flush()
        return await self._require_full(rule_id)

    async def delete_rule(self, rule_id: UUID) -> None:
        rule = await self._rules.get(rule_id)
        if rule is None:
            raise NotFoundError("Rule not found")
        rule.is_deleted = True
        self._log(rule_id, None, RuleHistoryAction.DELETED)
        await self._session.flush()

    # ------------------------------------------------------------- helpers
    async def _publish_and_activate(
        self, rule_id: UUID, version: RuleVersion
    ) -> None:
        if version.status == RuleStatus.PUBLISHED:
            raise ConflictError("Version is already published")
        errors = self._validator.validate_for_publish(version)
        if errors:
            raise ValidationError("; ".join(errors))
        # Deactivate / archive the currently active version *first* and flush,
        # so the "one active version per rule" partial unique index never sees
        # two active rows at once (the index is not deferrable).
        stmt = select(RuleVersion).where(
            RuleVersion.rule_id == rule_id,
            RuleVersion.is_active.is_(True),
            RuleVersion.is_deleted.is_(False),
        )
        deactivated = False
        for current in (await self._session.execute(stmt)).scalars().all():
            current.is_active = False
            current.status = RuleStatus.ARCHIVED
            deactivated = True
        if deactivated:
            await self._session.flush()
        version.status = RuleStatus.PUBLISHED
        version.is_active = True
        version.published_at = datetime.now(tz=UTC)
        await self._session.flush()
        self._log(rule_id, version.id, RuleHistoryAction.PUBLISHED)
        self._log(rule_id, version.id, RuleHistoryAction.ACTIVATED)

    def _build_version(
        self, number: int, content: VersionContentInput
    ) -> RuleVersion:
        version = RuleVersion(
            version_number=number,
            status=RuleStatus.DRAFT,
            priority=content.priority,
            is_active=False,
            effective_from=content.effective_from,
            effective_to=content.effective_to,
            notes=content.notes,
        )
        version.conditions = [
            RuleCondition(
                condition_type=c.condition_type, operator=c.operator,
                field=c.field, value=c.value,
            )
            for c in content.conditions
        ]
        version.actions = [
            RuleAction(
                action_type=a.action_type, parameters=a.parameters,
                sort_order=a.sort_order,
            )
            for a in content.actions
        ]
        version.resource_requirements = [
            ResourceRequirement(
                resource_category=r.resource_category,
                vehicle_type_code=r.vehicle_type_code,
                min_count=r.min_count,
                recommended_count=r.recommended_count,
                reserve_count=r.reserve_count,
                priority=r.priority,
                notes=r.notes,
            )
            for r in content.resource_requirements
        ]
        version.capability_requirements = [
            CapabilityRequirement(
                capability_code=c.capability_code,
                min_quantity=c.min_quantity,
                mandatory=c.mandatory,
            )
            for c in content.capability_requirements
        ]
        return version

    def _apply_links(self, rule: Rule, incident_type_ids, complexities, tags) -> None:
        rule.incident_types = [
            IncidentTypeRule(incident_type_id=i) for i in incident_type_ids
        ]
        rule.incident_categories = [
            IncidentCategoryRule(complexity=c) for c in complexities
        ]
        rule.tags = [RuleTag(tag=t) for t in tags]

    def _replace_links(self, rule: Rule, data: RuleUpdate) -> None:
        if data.incident_type_ids is not None:
            rule.incident_types = [
                IncidentTypeRule(incident_type_id=i) for i in data.incident_type_ids
            ]
        if data.complexities is not None:
            rule.incident_categories = [
                IncidentCategoryRule(complexity=c) for c in data.complexities
            ]
        if data.tags is not None:
            rule.tags = [RuleTag(tag=t) for t in data.tags]

    def _log(
        self, rule_id: UUID, version_id: UUID | None, action: RuleHistoryAction
    ) -> None:
        self._session.add(
            RuleHistory(rule_id=rule_id, rule_version_id=version_id, action=action)
        )

    async def _require_full(self, rule_id: UUID) -> Rule:
        rule = await self._rules.get_full(rule_id)
        if rule is None:  # pragma: no cover - just-created row
            raise NotFoundError("Rule not found")
        return rule


__all__ = ["RuleWriteService", "active_version"]
