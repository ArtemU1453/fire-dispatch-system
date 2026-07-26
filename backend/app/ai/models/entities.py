"""ORM model for the AI audit log.

Records **metadata only** about every AI call (stage §12): which provider and
model (and version) ran, the capability, success / error, the confidence, the
response and processing times, and the related call / incident. It deliberately
**does not store prompts or the conversation text**, per the security / data-
retention requirement.

References ``calls`` (Stage 11) and ``incidents`` (Stage 9) by id only; no earlier
stage is modified.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.ai.models.enums import AIAuditCapability, AIAuditStatus
from app.ai.models.types import ai_audit_capability_enum, ai_audit_status_enum
from app.models.base import Entity


class AIAuditLog(Entity):
    """One audit entry per AI invocation (metadata only — no prompt / text)."""

    __tablename__ = "ai_audit_log"
    __table_args__ = (
        Index("ix_ai_audit_capability_created", "capability", "created_at"),
        Index("ix_ai_audit_provider_created", "provider", "created_at"),
    )

    capability: Mapped[AIAuditCapability] = mapped_column(
        ai_audit_capability_enum, nullable=False, index=True
    )
    status: Mapped[AIAuditStatus] = mapped_column(
        ai_audit_status_enum, nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Provider-reported processing time and total service latency (ms).
    processing_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    error: Mapped[str | None] = mapped_column(String(512), nullable=True)
    call_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("calls.id", ondelete="SET NULL"), nullable=True, index=True
    )
    incident_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Non-sensitive metadata only (e.g. counts / flags) — never prompts or text.
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
