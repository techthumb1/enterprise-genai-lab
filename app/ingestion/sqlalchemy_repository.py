from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.models import (
    IngestionDraft,
    PersistedDocument,
)
from app.models.document import (
    Document,
    DocumentChunk,
    DocumentProcessingRun,
)


class SQLAlchemyIngestionRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def _find_document(
        self,
        checksum_sha256: str,
    ) -> Document | None:
        statement = select(Document).where(
            Document.checksum_sha256
            == checksum_sha256
        )

        result = await self._session.execute(
            statement
        )

        return result.scalar_one_or_none()

    async def _find_processing_run(
        self,
        *,
        document_id: UUID,
        checksum_sha256: str,
        strategy_key: str,
    ) -> PersistedDocument | None:
        statement = (
            select(
                DocumentProcessingRun.id.label(
                    "processing_run_id"
                ),
                func.count(
                    DocumentChunk.id
                ).label("chunk_count"),
            )
            .outerjoin(
                DocumentChunk,
                DocumentChunk.processing_run_id
                == DocumentProcessingRun.id,
            )
            .where(
                DocumentProcessingRun.document_id
                == document_id,
                DocumentProcessingRun.strategy_key
                == strategy_key,
            )
            .group_by(
                DocumentProcessingRun.id,
            )
        )

        result = await self._session.execute(
            statement
        )

        row = result.one_or_none()

        if row is None:
            return None

        return PersistedDocument(
            document_id=document_id,
            processing_run_id=(
                row.processing_run_id
            ),
            checksum_sha256=checksum_sha256,
            chunk_count=row.chunk_count,
            created=False,
        )

    async def _create_document(
        self,
        draft: IngestionDraft,
    ) -> Document:
        document = Document(
            filename=draft.filename,
            media_type=draft.media_type,
            checksum_sha256=(
                draft.checksum_sha256
            ),
            source_metadata=(
                draft.source_metadata
            ),
        )

        self._session.add(document)

        try:
            await self._session.flush()
        except IntegrityError:
            await self._session.rollback()

            existing = await self._find_document(
                draft.checksum_sha256
            )

            if existing is None:
                raise

            return existing

        return document

    async def save(
        self,
        draft: IngestionDraft,
    ) -> PersistedDocument:
        document = await self._find_document(
            draft.checksum_sha256
        )

        if document is None:
            document = await self._create_document(
                draft
            )

        document_id = document.id

        strategy_key = (
            draft.strategy.strategy_key
        )

        existing_run = (
            await self._find_processing_run(
                document_id=document_id,
                checksum_sha256=(
                    draft.checksum_sha256
                ),
                strategy_key=strategy_key,
            )
        )

        if existing_run is not None:
            return existing_run

        processing_run = DocumentProcessingRun(
            document_id=document_id,
            strategy_key=strategy_key,
            parser_name=(
                draft.strategy.parser_name
            ),
            parser_version=(
                draft.strategy.parser_version
            ),
            normalization_version=(
                draft.strategy.normalization_version
            ),
            chunker_name=(
                draft.strategy.chunker_name
            ),
            chunker_version=(
                draft.strategy.chunker_version
            ),
            chunking_config=(
                draft.strategy.chunking_config
            ),
            processing_metadata=(
                draft.processing_metadata
            ),
        )

        processing_run.chunks = [
            DocumentChunk(
                document_id=document_id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                section_title=(
                    chunk.section_title
                ),
                page_number=chunk.page_number,
                token_count=chunk.token_count,
                chunk_metadata={
                    **chunk.metadata,
                    "section_ordinal": (
                        chunk.section_ordinal
                    ),
                    "source_span": (
                        chunk.source_span.model_dump()
                    ),
                },
            )
            for chunk in draft.chunks
        ]

        self._session.add(processing_run)

        try:
            await self._session.flush()
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()

            existing_run = (
                await self._find_processing_run(
                    document_id=document_id,
                    checksum_sha256=(
                        draft.checksum_sha256
                    ),
                    strategy_key=strategy_key,
                )
            )

            if existing_run is None:
                raise

            return existing_run

        return PersistedDocument(
            document_id=document_id,
            processing_run_id=processing_run.id,
            checksum_sha256=(
                draft.checksum_sha256
            ),
            chunk_count=len(draft.chunks),
            created=True,
        )