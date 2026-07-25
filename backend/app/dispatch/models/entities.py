"""ORM models for persisted dispatch recommendations.

A **Recommendation** is the aggregate root: the advisory composition produced for
one incident. It owns the selected **items** (primary + reserve), their
**reasons**, a 1:1 **summary**, the per-capability **matches**, the full log of
evaluated **resource matches** (selected and excluded, with reasons), and a 1:1
**decision** record (the audit log — used rules, request snapshot).

Everything is advisory: nothing here dispatches a unit. All tables reuse the
Stage-2 ``Entity`` base (UUID PK, timestamps, soft-delete).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.dispatch.models.enums import (
    ConfidenceLevel,
    DispatchStatus,
    ExclusionReason,
    RecommendationRole,
)
from app.dispatch.models.types import (
    confidence_level_enum,
    dispatch_status_enum,
    exclusion_reason_enum,
    incident_complexity_enum,
    recommendation_role_enum,
    rule_priority_enum,
)
from app.models.base import Entity
from app.rules.models.enums import IncidentComplexity, RulePriority

if TYPE_CHECKING:
    from app.models.resource import Resource


class Recommendation(Entity):
    """The advisory composition produced for one incident."""

    __tablename__ = "dispatch_recommendations"
    __table_args__ = (
        Index("ix_dispatch_rec_incident", "incident_id", "created_at"),
    )

    incident_id: Mapped[UUID | None] = mapped_column(nullable=True, index=True)
    incident_type_id: Mapped[UUID] = mapped_column(
        ForeignKey("incident_types.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    complexity: Mapped[IncidentComplexity | None] = mapped_column(
        incident_complexity_enum, nullable=True
    )
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    administrative_area_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("administrative_areas.id", ondelete="SET NULL"), nullable=True
    )
    danger_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    priority: Mapped[RulePriority] = mapped_column(
        rule_priority_enum,
        server_default=RulePriority.NORMAL.value,
        nullable=False,
    )
    status: Mapped[DispatchStatus] = mapped_column(
        dispatch_status_enum, nullable=False, index=True
    )
    sufficient: Mapped[bool] = mapped_column(Boolean, nullable=False)
    confidence: Mapped[ConfidenceLevel] = mapped_column(
        confidence_level_enum, nullable=False
    )
    confidence_score: Mapped[float] = mapped_column(
        Float, server_default="0", nullable=False
    )
    total_candidates: Mapped[int] = mapped_column(
        Integer, server_default="0", nullable=False
    )
    is_preview: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False, index=True
    )

    items: Mapped[list[RecommendationItem]] = relationship(
        back_populates="recommendation", cascade="all, delete-orphan"
    )
    reasons: Mapped[list[RecommendationReason]] = relationship(
        back_populates="recommendation", cascade="all, delete-orphan"
    )
    resource_matches: Mapped[list[ResourceMatch]] = relationship(
        back_populates="recommendation", cascade="all, delete-orphan"
    )
    capability_matches: Mapped[list[CapabilityMatch]] = relationship(
        back_populates="recommendation", cascade="all, delete-orphan"
    )
    summary: Mapped[RecommendationSummary | None] = relationship(
        back_populates="recommendation",
        cascade="all, delete-orphan",
        uselist=False,
    )
    decision: Mapped[DispatchDecision | None] = relationship(
        back_populates="recommendation",
        cascade="all, delete-orphan",
        uselist=False,
    )


class RecommendationItem(Entity):
    """A selected unit (primary or reserve) with its ordering and score."""

    __tablename__ = "dispatch_recommendation_items"

    recommendation_id: Mapped[UUID] = mapped_column(
        ForeignKey("dispatch_recommendations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resource_id: Mapped[UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[RecommendationRole] = mapped_column(
        recommendation_role_enum, nullable=False
    )
    distance_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    readiness: Mapped[str] = mapped_column(String(32), nullable=False)
    sort_order: Mapped[int] = mapped_column(
        Integer, server_default="0", nullable=False
    )

    recommendation: Mapped[Recommendation] = relationship(back_populates="items")
    reasons: Mapped[list[RecommendationReason]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )
    resource: Mapped[Resource] = relationship(
        "Resource", viewonly=True, lazy="raise"
    )


class RecommendationReason(Entity):
    """An automatically generated explanation line for the recommendation.

    Attached to a single item (``item_id`` set) or to the recommendation as a
    whole (``item_id`` null — e.g. a coverage or sufficiency note).
    """

    __tablename__ = "dispatch_recommendation_reasons"

    recommendation_id: Mapped[UUID] = mapped_column(
        ForeignKey("dispatch_recommendations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("dispatch_recommendation_items.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    text: Mapped[str] = mapped_column(String(512), nullable=False)
    kind: Mapped[str | None] = mapped_column(String(32), nullable=True)

    recommendation: Mapped[Recommendation] = relationship(back_populates="reasons")
    item: Mapped[RecommendationItem | None] = relationship(back_populates="reasons")


class RecommendationSummary(Entity):
    """Roll-up figures for a recommendation (1:1)."""

    __tablename__ = "dispatch_recommendation_summaries"
    __table_args__ = (
        UniqueConstraint("recommendation_id", name="uq_dispatch_summary_rec"),
    )

    recommendation_id: Mapped[UUID] = mapped_column(
        ForeignKey("dispatch_recommendations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    primary_count: Mapped[int] = mapped_column(Integer, nullable=False)
    reserve_count: Mapped[int] = mapped_column(Integer, nullable=False)
    minimum_units: Mapped[int] = mapped_column(Integer, nullable=False)
    recommended_units: Mapped[int] = mapped_column(Integer, nullable=False)
    reserve_units: Mapped[int] = mapped_column(Integer, nullable=False)
    required_capabilities: Mapped[list[Any] | None] = mapped_column(
        JSONB, nullable=True
    )
    covered_capabilities: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    missing_capabilities: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    messages: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)

    recommendation: Mapped[Recommendation] = relationship(back_populates="summary")


class ResourceMatch(Entity):
    """Log of one evaluated resource — selected or excluded (with reason).

    Records every candidate the engine considered, so a recommendation is fully
    explainable: which resources were used and why others were excluded.
    """

    __tablename__ = "dispatch_resource_matches"

    recommendation_id: Mapped[UUID] = mapped_column(
        ForeignKey("dispatch_recommendations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resource_id: Mapped[UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    distance_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    readiness: Mapped[str] = mapped_column(String(32), nullable=False)
    selected: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    excluded: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    exclusion_reason: Mapped[ExclusionReason | None] = mapped_column(
        exclusion_reason_enum, nullable=True
    )
    detail: Mapped[str | None] = mapped_column(String(512), nullable=True)

    recommendation: Mapped[Recommendation] = relationship(
        back_populates="resource_matches"
    )
    resource: Mapped[Resource] = relationship(
        "Resource", viewonly=True, lazy="raise"
    )


class CapabilityMatch(Entity):
    """Coverage of one required capability by the selected composition."""

    __tablename__ = "dispatch_capability_matches"

    recommendation_id: Mapped[UUID] = mapped_column(
        ForeignKey("dispatch_recommendations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    capability_code: Mapped[str] = mapped_column(String(64), nullable=False)
    required_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    provided_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    satisfied: Mapped[bool] = mapped_column(Boolean, nullable=False)
    mandatory: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), nullable=False
    )

    recommendation: Mapped[Recommendation] = relationship(
        back_populates="capability_matches"
    )


class DispatchDecision(Entity):
    """Audit record of a recommendation run (1:1) — the decision log.

    ``decided`` is always ``False`` at this stage: the module only advises; the
    dispatcher makes the final decision. Stores the rules used, a snapshot of the
    request and free-form notes for traceability.
    """

    __tablename__ = "dispatch_decisions"
    __table_args__ = (
        UniqueConstraint("recommendation_id", name="uq_dispatch_decision_rec"),
    )

    recommendation_id: Mapped[UUID] = mapped_column(
        ForeignKey("dispatch_recommendations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    incident_id: Mapped[UUID | None] = mapped_column(nullable=True, index=True)
    decided: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    status: Mapped[DispatchStatus] = mapped_column(
        dispatch_status_enum, nullable=False
    )
    used_rule_ids: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    used_rule_codes: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    request_snapshot: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True
    )
    notes: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(nullable=True)

    recommendation: Mapped[Recommendation] = relationship(back_populates="decision")
