"""crisis management platform

Revision ID: b7e9d1c3f5a2
Revises: 74a0f4121e60
Create Date: 2026-07-27 00:00:00.000000+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b7e9d1c3f5a2"
down_revision: str | None = "74a0f4121e60"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TS = dict(server_default=sa.text("now()"), nullable=False)


def _audit_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), **_TS),
        sa.Column("updated_at", sa.DateTime(timezone=True), **_TS),
        sa.Column(
            "is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
    ]


def upgrade() -> None:
    # --- crisis_response_levels (configurable reference; §3) -----------------
    op.create_table(
        "crisis_response_levels",
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=True),
        *_audit_columns(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_crisis_response_levels_code"),
        "crisis_response_levels", ["code"], unique=True,
    )
    op.create_index(
        op.f("ix_crisis_response_levels_is_deleted"),
        "crisis_response_levels", ["is_deleted"], unique=False,
    )

    # --- crisis_operations ---------------------------------------------------
    op.create_table(
        "crisis_operations",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("response_level_id", sa.UUID(), nullable=True),
        sa.Column("incident_ref", sa.String(length=64), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(
            ["response_level_id"], ["crisis_response_levels.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_crisis_operations_code"), "crisis_operations", ["code"], unique=True
    )
    op.create_index(
        op.f("ix_crisis_operations_incident_ref"),
        "crisis_operations", ["incident_ref"], unique=False,
    )
    op.create_index(
        op.f("ix_crisis_operations_is_deleted"),
        "crisis_operations", ["is_deleted"], unique=False,
    )
    op.create_index(
        op.f("ix_crisis_operations_response_level_id"),
        "crisis_operations", ["response_level_id"], unique=False,
    )

    # --- crisis_headquarters -------------------------------------------------
    op.create_table(
        "crisis_headquarters",
        sa.Column("operation_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(
            ["operation_id"], ["crisis_operations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_crisis_headquarters_is_deleted"),
        "crisis_headquarters", ["is_deleted"], unique=False,
    )
    op.create_index(
        op.f("ix_crisis_headquarters_operation_id"),
        "crisis_headquarters", ["operation_id"], unique=True,
    )

    # --- crisis_command_assignments ------------------------------------------
    op.create_table(
        "crisis_command_assignments",
        sa.Column("headquarters_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("user_ref", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("responsibilities", sa.Text(), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(
            ["headquarters_id"], ["crisis_headquarters.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_crisis_command_assignments_headquarters_id"),
        "crisis_command_assignments", ["headquarters_id"], unique=False,
    )
    op.create_index(
        op.f("ix_crisis_command_assignments_is_deleted"),
        "crisis_command_assignments", ["is_deleted"], unique=False,
    )

    # --- crisis_sectors ------------------------------------------------------
    op.create_table(
        "crisis_sectors",
        sa.Column("operation_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("leader_ref", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("situation", sa.Text(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("center_lat", sa.Float(), nullable=True),
        sa.Column("center_lon", sa.Float(), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(
            ["operation_id"], ["crisis_operations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_crisis_sectors_is_deleted"),
        "crisis_sectors", ["is_deleted"], unique=False,
    )
    op.create_index(
        op.f("ix_crisis_sectors_operation_id"),
        "crisis_sectors", ["operation_id"], unique=False,
    )

    # --- crisis_zones --------------------------------------------------------
    op.create_table(
        "crisis_zones",
        sa.Column("operation_id", sa.UUID(), nullable=False),
        sa.Column("sector_id", sa.UUID(), nullable=True),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("center_lat", sa.Float(), nullable=True),
        sa.Column("center_lon", sa.Float(), nullable=True),
        sa.Column("radius_m", sa.Float(), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(
            ["operation_id"], ["crisis_operations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["sector_id"], ["crisis_sectors.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_crisis_zones_is_deleted"), "crisis_zones", ["is_deleted"], unique=False
    )
    op.create_index(
        op.f("ix_crisis_zones_operation_id"),
        "crisis_zones", ["operation_id"], unique=False,
    )
    op.create_index(
        op.f("ix_crisis_zones_sector_id"), "crisis_zones", ["sector_id"], unique=False
    )

    # --- crisis_plan_stages --------------------------------------------------
    op.create_table(
        "crisis_plan_stages",
        sa.Column("operation_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(
            ["operation_id"], ["crisis_operations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_crisis_plan_stages_is_deleted"),
        "crisis_plan_stages", ["is_deleted"], unique=False,
    )
    op.create_index(
        op.f("ix_crisis_plan_stages_operation_id"),
        "crisis_plan_stages", ["operation_id"], unique=False,
    )

    # --- crisis_tasks --------------------------------------------------------
    op.create_table(
        "crisis_tasks",
        sa.Column("operation_id", sa.UUID(), nullable=False),
        sa.Column("stage_id", sa.UUID(), nullable=True),
        sa.Column("sector_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("assignee_ref", sa.String(length=64), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(
            ["operation_id"], ["crisis_operations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["sector_id"], ["crisis_sectors.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["stage_id"], ["crisis_plan_stages.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_crisis_tasks_is_deleted"), "crisis_tasks", ["is_deleted"], unique=False
    )
    op.create_index(
        op.f("ix_crisis_tasks_operation_id"),
        "crisis_tasks", ["operation_id"], unique=False,
    )
    op.create_index(
        op.f("ix_crisis_tasks_sector_id"), "crisis_tasks", ["sector_id"], unique=False
    )
    op.create_index(
        op.f("ix_crisis_tasks_stage_id"), "crisis_tasks", ["stage_id"], unique=False
    )

    # --- crisis_resource_groups ----------------------------------------------
    op.create_table(
        "crisis_resource_groups",
        sa.Column("operation_id", sa.UUID(), nullable=False),
        sa.Column("sector_id", sa.UUID(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("purpose", sa.String(length=255), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(
            ["operation_id"], ["crisis_operations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["sector_id"], ["crisis_sectors.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_crisis_resource_groups_is_deleted"),
        "crisis_resource_groups", ["is_deleted"], unique=False,
    )
    op.create_index(
        op.f("ix_crisis_resource_groups_operation_id"),
        "crisis_resource_groups", ["operation_id"], unique=False,
    )
    op.create_index(
        op.f("ix_crisis_resource_groups_sector_id"),
        "crisis_resource_groups", ["sector_id"], unique=False,
    )

    # --- crisis_resource_group_members ---------------------------------------
    op.create_table(
        "crisis_resource_group_members",
        sa.Column("group_id", sa.UUID(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("ref", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(
            ["group_id"], ["crisis_resource_groups.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_crisis_resource_group_members_group_id"),
        "crisis_resource_group_members", ["group_id"], unique=False,
    )
    op.create_index(
        op.f("ix_crisis_resource_group_members_is_deleted"),
        "crisis_resource_group_members", ["is_deleted"], unique=False,
    )

    # --- crisis_resource_moves -----------------------------------------------
    op.create_table(
        "crisis_resource_moves",
        sa.Column("group_id", sa.UUID(), nullable=False),
        sa.Column("from_sector_id", sa.UUID(), nullable=True),
        sa.Column("to_sector_id", sa.UUID(), nullable=True),
        sa.Column("note", sa.String(length=512), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(
            ["from_sector_id"], ["crisis_sectors.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["group_id"], ["crisis_resource_groups.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["to_sector_id"], ["crisis_sectors.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_crisis_resource_moves_group_id"),
        "crisis_resource_moves", ["group_id"], unique=False,
    )
    op.create_index(
        op.f("ix_crisis_resource_moves_is_deleted"),
        "crisis_resource_moves", ["is_deleted"], unique=False,
    )

    # --- crisis_situation_reports --------------------------------------------
    op.create_table(
        "crisis_situation_reports",
        sa.Column("operation_id", sa.UUID(), nullable=False),
        sa.Column("author_ref", sa.String(length=64), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(
            ["operation_id"], ["crisis_operations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_crisis_situation_reports_is_deleted"),
        "crisis_situation_reports", ["is_deleted"], unique=False,
    )
    op.create_index(
        op.f("ix_crisis_situation_reports_operation_id"),
        "crisis_situation_reports", ["operation_id"], unique=False,
    )

    # --- crisis_operational_orders -------------------------------------------
    op.create_table(
        "crisis_operational_orders",
        sa.Column("operation_id", sa.UUID(), nullable=False),
        sa.Column("number", sa.String(length=64), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("issued_by_ref", sa.String(length=64), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(
            ["operation_id"], ["crisis_operations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_crisis_operational_orders_is_deleted"),
        "crisis_operational_orders", ["is_deleted"], unique=False,
    )
    op.create_index(
        op.f("ix_crisis_operational_orders_operation_id"),
        "crisis_operational_orders", ["operation_id"], unique=False,
    )

    # --- crisis_journal_entries (immutable unified journal; §8) --------------
    op.create_table(
        "crisis_journal_entries",
        sa.Column("operation_id", sa.UUID(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("actor_ref", sa.String(length=64), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(
            ["operation_id"], ["crisis_operations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_crisis_journal_entries_is_deleted"),
        "crisis_journal_entries", ["is_deleted"], unique=False,
    )
    op.create_index(
        op.f("ix_crisis_journal_entries_kind"),
        "crisis_journal_entries", ["kind"], unique=False,
    )
    op.create_index(
        op.f("ix_crisis_journal_entries_operation_id"),
        "crisis_journal_entries", ["operation_id"], unique=False,
    )

    # --- seed the configurable response levels (§3) --------------------------
    op.bulk_insert(
        sa.table(
            "crisis_response_levels",
            sa.column("id", sa.UUID()),
            sa.column("rank", sa.Integer()),
            sa.column("is_active", sa.Boolean()),
            sa.column("code", sa.String()),
            sa.column("name", sa.String()),
            sa.column("description", sa.String()),
        ),
        [
            {
                "id": _uuid(),
                "rank": rank,
                "is_active": True,
                "code": code,
                "name": name,
                "description": desc,
            }
            for rank, code, name, desc in _DEFAULT_LEVELS
        ],
    )


def downgrade() -> None:
    for table in (
        "crisis_journal_entries",
        "crisis_operational_orders",
        "crisis_situation_reports",
        "crisis_resource_moves",
        "crisis_resource_group_members",
        "crisis_resource_groups",
        "crisis_tasks",
        "crisis_plan_stages",
        "crisis_zones",
        "crisis_sectors",
        "crisis_command_assignments",
        "crisis_headquarters",
        "crisis_operations",
        "crisis_response_levels",
    ):
        op.drop_table(table)


import uuid  # noqa: E402


def _uuid() -> str:
    return str(uuid.uuid4())


_DEFAULT_LEVELS = [
    (0, "routine", "Повседневный режим", "Обычная работа службы"),
    (1, "heightened", "Повышенная готовность", "Повышенная готовность сил и средств"),
    (2, "emergency", "Чрезвычайная ситуация", "Режим чрезвычайной ситуации"),
    (3, "large_scale", "Крупномасштабная операция",
     "Крупномасштабная операция с привлечением значительных сил"),
]
