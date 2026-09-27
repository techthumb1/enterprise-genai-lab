"""add document processing runs

Revision ID: ab8e0275ae7b
Revises: 8841142943bc
Create Date: 2026-09-26 16:20:21.078329
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "ab8e0275ae7b"
down_revision: str | Sequence[str] | None = "8841142943bc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add versioned document processing runs."""

    op.create_table(
        "document_processing_runs",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("uuidv7()"),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "strategy_key",
            sa.String(length=512),
            nullable=False,
        ),
        sa.Column(
            "parser_name",
            sa.String(length=128),
            nullable=False,
        ),
        sa.Column(
            "parser_version",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "normalization_version",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "chunker_name",
            sa.String(length=128),
            nullable=False,
        ),
        sa.Column(
            "chunker_version",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "chunking_config",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "processing_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_id",
            "strategy_key",
            name="uq_document_processing_strategy",
        ),
    )

    op.create_index(
        op.f("ix_document_processing_runs_document_id"),
        "document_processing_runs",
        ["document_id"],
        unique=False,
    )

    op.add_column(
        "document_chunks",
        sa.Column(
            "processing_run_id",
            sa.UUID(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_document_chunks_processing_run_id",
        "document_chunks",
        "document_processing_runs",
        ["processing_run_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_index(
        op.f("ix_document_chunks_processing_run_id"),
        "document_chunks",
        ["processing_run_id"],
        unique=False,
    )

    # Backfill one baseline processing run for every existing document.
    #
    # Parser and normalization identity were persisted on the source
    # document. Chunk metadata also preserved the baseline chunker and
    # tokenizer identity, but not its complete constructor configuration.
    op.execute(
        sa.text(
            """
            INSERT INTO document_processing_runs (
                id,
                document_id,
                strategy_key,
                parser_name,
                parser_version,
                normalization_version,
                chunker_name,
                chunker_version,
                chunking_config,
                processing_metadata
            )
            SELECT
                uuidv7(),
                d.id,
                'legacy-baseline-v1',
                COALESCE(
                    d.source_metadata -> 'parser' ->> 'name',
                    'unknown'
                ),
                COALESCE(
                    d.source_metadata -> 'parser' ->> 'version',
                    'unknown'
                ),
                COALESCE(
                    d.source_metadata ->> 'normalization_version',
                    'unknown'
                ),
                COALESCE(
                    (
                        SELECT dc.chunk_metadata ->> 'chunker'
                        FROM document_chunks AS dc
                        WHERE dc.document_id = d.id
                        ORDER BY dc.chunk_index
                        LIMIT 1
                    ),
                    'unknown'
                ),
                COALESCE(
                    (
                        SELECT dc.chunk_metadata ->> 'chunker_version'
                        FROM document_chunks AS dc
                        WHERE dc.document_id = d.id
                        ORDER BY dc.chunk_index
                        LIMIT 1
                    ),
                    'unknown'
                ),
                '{}'::jsonb,
                jsonb_build_object(
                    'migration_backfill',
                    true,
                    'chunking_config_recovered',
                    false,
                    'tokenizer',
                    COALESCE(
                        (
                            SELECT dc.chunk_metadata ->> 'tokenizer'
                            FROM document_chunks AS dc
                            WHERE dc.document_id = d.id
                            ORDER BY dc.chunk_index
                            LIMIT 1
                        ),
                        'unknown'
                    )
                )
            FROM documents AS d
            """
        )
    )

    op.execute(
        sa.text(
            """
            UPDATE document_chunks AS dc
            SET processing_run_id = dpr.id
            FROM document_processing_runs AS dpr
            WHERE dpr.document_id = dc.document_id
              AND dpr.strategy_key = 'legacy-baseline-v1'
            """
        )
    )


def downgrade() -> None:
    """Remove versioned document processing runs."""

    op.drop_index(
        op.f("ix_document_chunks_processing_run_id"),
        table_name="document_chunks",
    )

    op.drop_constraint(
        "fk_document_chunks_processing_run_id",
        "document_chunks",
        type_="foreignkey",
    )

    op.drop_column(
        "document_chunks",
        "processing_run_id",
    )

    op.drop_index(
        op.f("ix_document_processing_runs_document_id"),
        table_name="document_processing_runs",
    )

    op.drop_table("document_processing_runs")