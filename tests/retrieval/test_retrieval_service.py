from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

import pytest

from app.retrieval.models import (
    ChunkForEmbedding,
    EmbeddingBatch,
    RetrievalHit,
)
from app.retrieval.service import RetrievalService

PROCESSING_RUN_ID = UUID(
    "018f0000-0000-7000-8000-000000000010"
)

CHUNK_ID = UUID("018f0000-0000-7000-8000-000000000001")
DOCUMENT_ID = UUID("018f0000-0000-7000-8000-000000000002")


class FakeProvider:
    provider = "test"
    model = "test-embedding"

    async def embed(
        self,
        texts: Sequence[str],
    ) -> EmbeddingBatch:
        return EmbeddingBatch(
            provider=self.provider,
            model=self.model,
            dimensions=3,
            vectors=((1.0, 0.0, 0.0),),
        )


class FakeRepository:
    async def pending_chunks(
        self,
        *,
        processing_run_id: UUID,
        provider: str,
        model: str,
        limit: int,
    ) -> tuple[ChunkForEmbedding, ...]:
        return ()

    async def store_embeddings(
        self,
        *,
        chunks: Sequence[ChunkForEmbedding],
        batch: EmbeddingBatch,
    ) -> int:
        return 0

    async def lexical_search(
        self,
        *,
        processing_run_id: UUID,
        query: str,
        limit: int,
    ) -> tuple[RetrievalHit, ...]:
        return (
            RetrievalHit(
                chunk_id=CHUNK_ID,
                document_id=DOCUMENT_ID,
                content="lexical result",
                score=0.8,
            ),
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
        return (
            RetrievalHit(
                chunk_id=CHUNK_ID,
                document_id=DOCUMENT_ID,
                content="vector result",
                score=0.9,
            ),
        )


@pytest.mark.asyncio
async def test_retrieval_service_searches_both_modes() -> None:
    service = RetrievalService(
        repository=FakeRepository(),
        embedding_provider=FakeProvider(),
    )

    lexical = await service.lexical_search(
        processing_run_id=PROCESSING_RUN_ID,
        query="knowledge graph",
    )

    vector = await service.vector_search(
        processing_run_id=PROCESSING_RUN_ID,
        query="knowledge graph",
    )

    assert lexical[0].score == 0.8
    assert vector[0].score == 0.9