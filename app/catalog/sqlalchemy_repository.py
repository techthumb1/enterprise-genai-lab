from __future__ import annotations

from sqlalchemy import and_, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog.models import ProcessingRunSummary
from app.models.document import Document, DocumentChunk, DocumentProcessingRun
from app.models.embedding import ChunkEmbedding


class SQLAlchemyProcessingRunCatalog:
    def __init__(
        self,
        session: AsyncSession,
        *,
        embedding_provider: str,
        embedding_model: str,
    ) -> None:
        self._session = session
        self._embedding_provider = embedding_provider
        self._embedding_model = embedding_model

    async def list_runs(
        self,
        *,
        ready_only: bool,
        limit: int,
    ) -> tuple[ProcessingRunSummary, ...]:
        chunk_count = func.count(distinct(DocumentChunk.id))
        embedded_chunk_count = func.count(distinct(ChunkEmbedding.chunk_id))

        statement = (
            select(
                DocumentProcessingRun.id,
                DocumentProcessingRun.document_id,
                Document.filename,
                DocumentProcessingRun.parser_name,
                DocumentProcessingRun.parser_version,
                DocumentProcessingRun.chunker_name,
                DocumentProcessingRun.chunker_version,
                DocumentProcessingRun.created_at,
                chunk_count.label("chunk_count"),
                embedded_chunk_count.label("embedded_chunk_count"),
            )
            .join(Document, Document.id == DocumentProcessingRun.document_id)
            .outerjoin(
                DocumentChunk,
                DocumentChunk.processing_run_id == DocumentProcessingRun.id,
            )
            .outerjoin(
                ChunkEmbedding,
                and_(
                    ChunkEmbedding.chunk_id == DocumentChunk.id,
                    ChunkEmbedding.provider == self._embedding_provider,
                    ChunkEmbedding.model == self._embedding_model,
                ),
            )
            .group_by(
                DocumentProcessingRun.id,
                DocumentProcessingRun.document_id,
                Document.filename,
                DocumentProcessingRun.parser_name,
                DocumentProcessingRun.parser_version,
                DocumentProcessingRun.chunker_name,
                DocumentProcessingRun.chunker_version,
                DocumentProcessingRun.created_at,
            )
            .order_by(
                DocumentProcessingRun.created_at.desc(),
                DocumentProcessingRun.id.desc(),
            )
            .limit(limit)
        )

        if ready_only:
            statement = statement.having(
                chunk_count > 0,
                embedded_chunk_count == chunk_count,
            )

        result = await self._session.execute(statement)

        return tuple(
            ProcessingRunSummary(
                id=row.id,
                document_id=row.document_id,
                filename=row.filename,
                parser_name=row.parser_name,
                parser_version=row.parser_version,
                chunker_name=row.chunker_name,
                chunker_version=row.chunker_version,
                chunk_count=row.chunk_count,
                embedded_chunk_count=row.embedded_chunk_count,
                embedding_provider=self._embedding_provider,
                embedding_model=self._embedding_model,
                ready_for_retrieval=(
                    row.chunk_count > 0
                    and row.embedded_chunk_count == row.chunk_count
                ),
                created_at=row.created_at,
            )
            for row in result
        )
