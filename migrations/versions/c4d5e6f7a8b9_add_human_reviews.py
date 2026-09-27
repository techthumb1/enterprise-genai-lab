"""add governed human review records

Revision ID: c4d5e6f7a8b9
Revises: ab8e0275ae7b
Create Date: 2026-09-27 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c4d5e6f7a8b9"
down_revision: str | Sequence[str] | None = "ab8e0275ae7b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "human_reviews",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("uuidv7()"),
            nullable=False,
        ),
        sa.Column("workflow_id", sa.UUID(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "candidate_answer",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "evidence",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("reviewer_id", sa.String(length=255), nullable=True),
        sa.Column("reviewer_comment", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="ck_human_reviews_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workflow_id"),
    )
    op.create_index(
        op.f("ix_human_reviews_status"),
        "human_reviews",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_human_reviews_workflow_id"),
        "human_reviews",
        ["workflow_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_human_reviews_workflow_id"), table_name="human_reviews"
    )
    op.drop_index(op.f("ix_human_reviews_status"), table_name="human_reviews")
    op.drop_table("human_reviews")
