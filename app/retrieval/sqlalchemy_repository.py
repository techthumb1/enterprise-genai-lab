from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import ColumnElement, func, literal_column, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import DocumentChunk
from app.models.embedding import ChunkEmbedding
from app.retrieval.models import (
    ChunkForEmbedding,
    EmbeddingBatch,
    RetrievalHit,
)


class SQLAlchemyRetrievalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def pending_chunks(
        self,
        *,
        processing_run_id: UUID,
        provider: str,
        model: str,
        limit: int,
    ) -> tuple[ChunkForEmbedding, ...]:
        already_embedded = (
            select(ChunkEmbedding.id)
            .where(
                ChunkEmbedding.chunk_id == DocumentChunk.id,
                ChunkEmbedding.provider == provider,
                ChunkEmbedding.model == model,
            )
            .exists()
        )

        statement = (
            select(
                DocumentChunk.id,
                DocumentChunk.content,
            )
            .where(
    DocumentChunk.processing_run_id == processing_run_id,
    ~already_embedded,
)
            .order_by(
                DocumentChunk.created_at,
                DocumentChunk.chunk_index,
            )
            .limit(limit)
        )

        result = await self._session.execute(statement)

        return tuple(
            ChunkForEmbedding(
                chunk_id=row.id,
                content=row.content,
            )
            for row in result
        )

    async def store_embeddings(
        self,
        *,
        chunks: Sequence[ChunkForEmbedding],
        batch: EmbeddingBatch,
    ) -> int:
        if len(chunks) != len(batch.vectors):
            raise ValueError(
                "chunk and embedding counts must match"
            )

        if not chunks:
            return 0

        rows = [
            {
                "chunk_id": chunk.chunk_id,
                "provider": batch.provider,
                "model": batch.model,
                "dimensions": batch.dimensions,
                "embedding": list(vector),
            }
            for chunk, vector in zip(
                chunks,
                batch.vectors,
                strict=True,
            )
        ]

        statement = (
            insert(ChunkEmbedding)
            .values(rows)
            .on_conflict_do_nothing(
                constraint="uq_chunk_embedding_model"
            )
            .returning(ChunkEmbedding.id)
        )

        result = await self._session.execute(statement)
        inserted = len(result.scalars().all())

        await self._session.commit()

        return inserted

    async def lexical_search(
        self,
        *,
        processing_run_id: UUID,
        query: str,
        limit: int,
    ) -> tuple[RetrievalHit, ...]:
        english: ColumnElement[object] = literal_column(
    "'english'::regconfig"
)

        document_vector = func.to_tsvector(
            english,
            DocumentChunk.content,
        )

        ts_query = func.plainto_tsquery(
            english,
            query,
        )

        rank = func.ts_rank_cd(
            document_vector,
            ts_query,
        )

        statement = (
            select(
                DocumentChunk.id.label("chunk_id"),
                DocumentChunk.document_id,
                DocumentChunk.content,
                rank.label("score"),
            )
            .where(
    DocumentChunk.processing_run_id == processing_run_id,
    document_vector.op("@@")(ts_query),
)
            .order_by(rank.desc())
            .limit(limit)
        )

        result = await self._session.execute(statement)

        return tuple(
            RetrievalHit(
                chunk_id=row.chunk_id,
                document_id=row.document_id,
                content=row.content,
                score=float(row.score),
            )
            for row in result
        )

    async def vector_search(
        self,
        *,
        processing_run_id: UUID,
        vector: Sequence[float],
        provider: str,
        model: str,
        dimensions: int,
        limit: int,
    ) -> tuple[RetrievalHit, ...]:
        distance = ChunkEmbedding.embedding.cosine_distance(
            list(vector)
        )

        similarity = 1 - distance

        statement = (
            select(
                DocumentChunk.id.label("chunk_id"),
                DocumentChunk.document_id,
                DocumentChunk.content,
                similarity.label("score"),
            )
            .join(
                ChunkEmbedding,
                ChunkEmbedding.chunk_id == DocumentChunk.id,
            )
            .where(
                DocumentChunk.processing_run_id == processing_run_id,
                ChunkEmbedding.provider == provider,
                ChunkEmbedding.model == model,
                ChunkEmbedding.dimensions == dimensions,
            )
            .order_by(distance)
            .limit(limit)
        )

        result = await self._session.execute(statement)

        return tuple(
            RetrievalHit(
                chunk_id=row.chunk_id,
                document_id=row.document_id,
                content=row.content,
                score=float(row.score),
            )
            for row in result
        )