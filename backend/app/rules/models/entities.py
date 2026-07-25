"""ORM models for the rules infrastructure.

A **Rule** is a logical normative; its content is carried by immutable
**RuleVersion**s (versioning). A version holds **conditions** (applicability),
**actions** (prescriptions) and structured **resource / capability requirements**.
Rules are grouped in **rule sets**, classified by **category**, tagged, linked to
incident types / complexity categories, and their lifecycle is audited in
**rule history**.

Rules describe *requirements*, never concrete units — no foreign keys to
resources. All tables reuse the Stage-2 ``Entity`` base (UUID PK, timestamps,
soft-delete).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import CatalogEntity, Entity
from app.models.enums import ResourceCategory
from app.rules.models.enums import (
    ActionType,
    ConditionOperator,
    ConditionType,
    IncidentComplexity,
    RuleHistoryAction,
    RulePriority,
    RuleStatus,
)
from app.rules.models.types import (
    action_type_enum,
    condition_operator_enum,
    condition_type_enum,
    history_action_enum,
    incident_complexity_enum,
    resource_category_enum,
    rule_priority_enum,
    rule_status_enum,
)


class RuleCategory(CatalogEntity):
    """A category of rules (fires, road accidents, rescue, …). Extensible."""

    __tablename__ = "rule_categories"

    rules: Mapped[list[Rule]] = relationship(back_populates="category")


class RuleSet(CatalogEntity):
    """A named grouping of rules (e.g. a normative document / order)."""

    __tablename__ = "rule_sets"

    rules: Mapped[list[Rule]] = relationship(back_populates="rule_set")


class Rule(Entity):
    """A logical normative rule; its content lives in versions."""

    __tablename__ = "rules"

    code: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), nullable=False
    )
    category_id: Mapped[UUID] = mapped_column(
        ForeignKey("rule_categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    rule_set_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("rule_sets.id", ondelete="SET NULL"), nullable=True, index=True
    )

    category: Mapped[RuleCategory] = relationship(back_populates="rules")
    rule_set: Mapped[RuleSet | None] = relationship(back_populates="rules")
    versions: Mapped[list[RuleVersion]] = relationship(
        back_populates="rule", cascade="all, delete-orphan"
    )
    tags: Mapped[list[RuleTag]] = relationship(
        back_populates="rule", cascade="all, delete-orphan"
    )
    incident_types: Mapped[list[IncidentTypeRule]] = relationship(
        back_populates="rule", cascade="all, delete-orphan"
    )
    incident_categories: Mapped[list[IncidentCategoryRule]] = relationship(
        back_populates="rule", cascade="all, delete-orphan"
    )
    history: Mapped[list[RuleHistory]] = relationship(
        back_populates="rule", cascade="all, delete-orphan"
    )


class RuleVersion(Entity):
    """An immutable version of a rule's content. One version may be *active*."""

    __tablename__ = "rule_versions"
    __table_args__ = (
        UniqueConstraint("rule_id", "version_number", name="uq_rule_version_number"),
        # At most one active version per rule.
        Index(
            "uq_rule_active_version",
            "rule_id",
            unique=True,
            postgresql_where=text("is_active AND NOT is_deleted"),
        ),
    )

    rule_id: Mapped[UUID] = mapped_column(
        ForeignKey("rules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[RuleStatus] = mapped_column(
        rule_status_enum,
        server_default=RuleStatus.DRAFT.value,
        nullable=False,
        index=True,
    )
    priority: Mapped[RulePriority] = mapped_column(
        rule_priority_enum,
        server_default=RulePriority.NORMAL.value,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False, index=True
    )
    effective_from: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    effective_to: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    published_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    rule: Mapped[Rule] = relationship(back_populates="versions")
    conditions: Mapped[list[RuleCondition]] = relationship(
        back_populates="version", cascade="all, delete-orphan"
    )
    actions: Mapped[list[RuleAction]] = relationship(
        back_populates="version", cascade="all, delete-orphan"
    )
    resource_requirements: Mapped[list[ResourceRequirement]] = relationship(
        back_populates="version", cascade="all, delete-orphan"
    )
    capability_requirements: Mapped[list[CapabilityRequirement]] = relationship(
        back_populates="version", cascade="all, delete-orphan"
    )


class RuleCondition(Entity):
    """An applicability condition of a rule version (heterogeneous value)."""

    __tablename__ = "rule_conditions"

    rule_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("rule_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    condition_type: Mapped[ConditionType] = mapped_column(
        condition_type_enum, nullable=False
    )
    operator: Mapped[ConditionOperator] = mapped_column(
        condition_operator_enum, nullable=False
    )
    field: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # Heterogeneous by nature (scalar / list / range) — JSONB is justified here.
    value: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    version: Mapped[RuleVersion] = relationship(back_populates="conditions")


class RuleAction(Entity):
    """A prescription attached to a rule version (generic, JSONB parameters)."""

    __tablename__ = "rule_actions"

    rule_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("rule_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action_type: Mapped[ActionType] = mapped_column(
        action_type_enum, nullable=False
    )
    parameters: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)

    version: Mapped[RuleVersion] = relationship(back_populates="actions")


class ResourceRequirement(Entity):
    """Required composition described by category — never concrete units."""

    __tablename__ = "rule_resource_requirements"

    rule_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("rule_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resource_category: Mapped[ResourceCategory] = mapped_column(
        resource_category_enum, nullable=False
    )
    vehicle_type_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    min_count: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    recommended_count: Mapped[int] = mapped_column(
        Integer, server_default="0", nullable=False
    )
    reserve_count: Mapped[int] = mapped_column(
        Integer, server_default="0", nullable=False
    )
    priority: Mapped[RulePriority] = mapped_column(
        rule_priority_enum,
        server_default=RulePriority.NORMAL.value,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(String(512), nullable=True)

    version: Mapped[RuleVersion] = relationship(back_populates="resource_requirements")


class CapabilityRequirement(Entity):
    """A required capability (by code — decoupled from catalog seeding)."""

    __tablename__ = "rule_capability_requirements"
    __table_args__ = (
        UniqueConstraint(
            "rule_version_id", "capability_code", name="uq_rule_capability_req"
        ),
    )

    rule_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("rule_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    capability_code: Mapped[str] = mapped_column(String(64), nullable=False)
    min_quantity: Mapped[int] = mapped_column(
        Integer, server_default="1", nullable=False
    )
    mandatory: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), nullable=False
    )

    version: Mapped[RuleVersion] = relationship(
        back_populates="capability_requirements"
    )


class IncidentTypeRule(Entity):
    """Junction: incident types a rule applies to (references Stage-2 catalog)."""

    __tablename__ = "rule_incident_types"
    __table_args__ = (
        UniqueConstraint("rule_id", "incident_type_id", name="uq_rule_incident_type"),
    )

    rule_id: Mapped[UUID] = mapped_column(
        ForeignKey("rules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    incident_type_id: Mapped[UUID] = mapped_column(
        ForeignKey("incident_types.id", ondelete="CASCADE"), nullable=False, index=True
    )

    rule: Mapped[Rule] = relationship(back_populates="incident_types")


class IncidentCategoryRule(Entity):
    """Junction: incident complexity categories a rule applies to."""

    __tablename__ = "rule_incident_categories"
    __table_args__ = (
        UniqueConstraint("rule_id", "complexity", name="uq_rule_incident_category"),
    )

    rule_id: Mapped[UUID] = mapped_column(
        ForeignKey("rules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    complexity: Mapped[IncidentComplexity] = mapped_column(
        incident_complexity_enum, nullable=False
    )

    rule: Mapped[Rule] = relationship(back_populates="incident_categories")


class RuleTag(Entity):
    """A free-form tag applied to a rule."""

    __tablename__ = "rule_tags"
    __table_args__ = (UniqueConstraint("rule_id", "tag", name="uq_rule_tag"),)

    rule_id: Mapped[UUID] = mapped_column(
        ForeignKey("rules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tag: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    rule: Mapped[Rule] = relationship(back_populates="tags")


class RuleHistory(Entity):
    """Append-only audit of a rule's lifecycle events."""

    __tablename__ = "rule_history"
    __table_args__ = (
        Index("ix_rule_history_rule_time", "rule_id", "occurred_at"),
    )

    rule_id: Mapped[UUID] = mapped_column(
        ForeignKey("rules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rule_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("rule_versions.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[RuleHistoryAction] = mapped_column(
        history_action_enum, nullable=False, index=True
    )
    changed_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    changes: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    rule: Mapped[Rule] = relationship(back_populates="history")
