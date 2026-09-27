# tests/ingestion/test_sqlalchemy_repository.py

from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import delete, func, select

from app.db.session import get_session_factory
from app.ingestion.chunking.fixed_window import FixedWindowChunker
from app.ingestion.hashing import sha256_bytes
from app.ingestion.models import (
    IngestionDraft,
    ProcessingStrategy,
)
from app.ingestion.parsers.text import TextParser
from app.ingestion.sqlalchemy_repository import SQLAlchemyIngestionRepository
from app.models.document import (
    Document,
    DocumentChunk,
    DocumentProcessingRun,
)

pytestmark = pytest.mark.skipif(
    "DATABASE_URL" not in os.environ,
    reason="DATABASE_URL is required for PostgreSQL integration tests",
)


@pytest.mark.asyncio
async def test_repository_persists_and_deduplicates_document() -> None:
    unique_text = (
        "Enterprise document intelligence integration test "
        f"{uuid.uuid4()}"
    )
    content = unique_text.encode("utf-8")
    checksum = sha256_bytes(content)

    parser = TextParser()
    parsed = parser.parse(
        filename="integration-test.txt",
        media_type="text/plain",
        content=content,
    )

    chunker = FixedWindowChunker()
    chunks = chunker.chunk(parsed)

    draft = IngestionDraft(
        filename="integration-test.txt",
        media_type="text/plain",
        checksum_sha256=checksum,
        strategy=ProcessingStrategy(
            parser_name=parsed.parser_name,
            parser_version=parsed.parser_version,
            normalization_version=parsed.normalization_version,
            chunker_name=chunker.name,
            chunker_version=chunker.version,
            chunking_config=chunker.config,
        ),
        source_metadata={
            "test": True,
        },
        sections=parsed.sections,
        chunks=chunks,
    )

    try:
        async with get_session_factory()() as session:
            repository = SQLAlchemyIngestionRepository(session)

            first = await repository.save(draft)

            assert first.created is True
            assert first.checksum_sha256 == checksum
            assert first.chunk_count == len(chunks)
            assert first.processing_run_id is not None

        async with get_session_factory()() as session:
            repository = SQLAlchemyIngestionRepository(session)

            duplicate = await repository.save(draft)

            assert duplicate.document_id == first.document_id
            assert duplicate.processing_run_id == first.processing_run_id
            assert duplicate.checksum_sha256 == checksum
            assert duplicate.chunk_count == len(chunks)
            assert duplicate.created is False

            document_count = await session.scalar(
                select(func.count(Document.id)).where(
                    Document.checksum_sha256 == checksum
                )
            )

            chunk_count = await session.scalar(
                select(func.count(DocumentChunk.id)).where(
                    DocumentChunk.document_id == first.document_id
                )
            )

            assert document_count == 1
            assert chunk_count == len(chunks)

    finally:
        async with get_session_factory()() as session:
            await session.execute(
                delete(Document).where(
                    Document.checksum_sha256 == checksum
                )
            )
            await session.commit()

@pytest.mark.asyncio
async def test_repository_versions_processing_strategy_for_same_document() -> None:
    unique_text = (
        "Enterprise document intelligence processing strategy test "
        f"{uuid.uuid4()} alpha beta gamma delta epsilon zeta eta theta"
    )
    content = unique_text.encode("utf-8")
    checksum = sha256_bytes(content)

    parser = TextParser()
    parsed = parser.parse(
        filename="strategy-test.txt",
        media_type="text/plain",
        content=content,
    )

    baseline_chunker = FixedWindowChunker(
        max_tokens=320,
        overlap_tokens=40,
    )
    baseline_chunks = baseline_chunker.chunk(parsed)

    candidate_chunker = FixedWindowChunker(
        max_tokens=5,
        overlap_tokens=1,
    )
    candidate_chunks = candidate_chunker.chunk(parsed)

    baseline_draft = IngestionDraft(
        filename="strategy-test.txt",
        media_type="text/plain",
        checksum_sha256=checksum,
        strategy=ProcessingStrategy(
            parser_name=parsed.parser_name,
            parser_version=parsed.parser_version,
            normalization_version=parsed.normalization_version,
            chunker_name=baseline_chunker.name,
            chunker_version=baseline_chunker.version,
            chunking_config=baseline_chunker.config,
        ),
        source_metadata={
            "test": True,
        },
        sections=parsed.sections,
        chunks=baseline_chunks,
    )

    candidate_draft = IngestionDraft(
        filename="strategy-test.txt",
        media_type="text/plain",
        checksum_sha256=checksum,
        strategy=ProcessingStrategy(
            parser_name=parsed.parser_name,
            parser_version=parsed.parser_version,
            normalization_version=parsed.normalization_version,
            chunker_name=candidate_chunker.name,
            chunker_version=candidate_chunker.version,
            chunking_config=candidate_chunker.config,
        ),
        source_metadata={
            "test": True,
        },
        sections=parsed.sections,
        chunks=candidate_chunks,
    )

    try:
        async with get_session_factory()() as session:
            repository = SQLAlchemyIngestionRepository(session)

            baseline = await repository.save(baseline_draft)

        async with get_session_factory()() as session:
            repository = SQLAlchemyIngestionRepository(session)

            candidate = await repository.save(candidate_draft)

            assert candidate.created is True

            assert candidate.document_id == baseline.document_id
            assert candidate.processing_run_id != baseline.processing_run_id

            document_count = await session.scalar(
                select(func.count(Document.id)).where(
                    Document.checksum_sha256 == checksum
                )
            )

            processing_run_count = await session.scalar(
                select(func.count(DocumentProcessingRun.id)).where(
                    DocumentProcessingRun.document_id == baseline.document_id
                )
            )

            chunk_count = await session.scalar(
                select(func.count(DocumentChunk.id)).where(
                    DocumentChunk.document_id == baseline.document_id
                )
            )

            assert document_count == 1
            assert processing_run_count == 2
            assert chunk_count == (
                len(baseline_chunks)
                + len(candidate_chunks)
            )

    finally:
        async with get_session_factory()() as session:
            await session.execute(
                delete(Document).where(
                    Document.checksum_sha256 == checksum
                )
            )
            await session.commit()
