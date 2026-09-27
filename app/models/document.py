from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuidv7()"),
    )

    filename: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )

    media_type: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    checksum_sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    source_metadata: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    processing_runs: Mapped[list[DocumentProcessingRun]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )

    chunks: Mapped[list[DocumentChunk]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )


class DocumentProcessingRun(Base):
    __tablename__ = "document_processing_runs"

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "strategy_key",
            name="uq_document_processing_strategy",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuidv7()"),
    )

    document_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "documents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    strategy_key: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )

    parser_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    parser_version: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    normalization_version: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    chunker_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    chunker_version: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    chunking_config: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )

    processing_metadata: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    document: Mapped[Document] = relationship(
        back_populates="processing_runs",
    )

    chunks: Mapped[list[DocumentChunk]] = relationship(
        back_populates="processing_run",
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuidv7()"),
    )

    document_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "documents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    processing_run_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "document_processing_runs.id",
            ondelete="CASCADE",
        ),
        nullable=True,
        index=True,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    section_title: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    page_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    token_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    chunk_metadata: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    document: Mapped[Document] = relationship(
        back_populates="chunks",
    )

    processing_run: Mapped[DocumentProcessingRun | None] = relationship(
        back_populates="chunks",
    )