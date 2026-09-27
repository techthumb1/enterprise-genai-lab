from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from app.retrieval.models import (
    ChunkForEmbedding,
    EmbeddingBatch,
    RetrievalHit,
)


class RetrievalRepository(Protocol):
    async def pending_chunks(
    self,
    *,
    processing_run_id: UUID,
    provider: str,
    model: str,
    limit: int,
) -> tuple[ChunkForEmbedding, ...]:
        ...

    async def store_embeddings(
        self,
        *,
        chunks: Sequence[ChunkForEmbedding],
        batch: EmbeddingBatch,
    ) -> int:
        ...

    async def lexical_search(
        self,
        *,
        processing_run_id: UUID,
        query: str,
        limit: int,
    ) -> tuple[RetrievalHit, ...]:
        ...

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
        ...