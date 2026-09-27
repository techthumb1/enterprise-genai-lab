from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

import pytest

from app.retrieval.embedding_service import EmbeddingService
from app.retrieval.models import (
    ChunkForEmbedding,
    EmbeddingBatch,
    RetrievalHit,
)

PROCESSING_RUN_ID = UUID(
    "018f0000-0000-7000-8000-000000000010"
)


class FakeProvider:
    provider = "test"
    model = "test-embedding-v1"

    async def embed(
        self,
        texts: Sequence[str],
    ) -> EmbeddingBatch:
        return EmbeddingBatch(
            provider=self.provider,
            model=self.model,
            dimensions=3,
            vectors=tuple(
                (1.0, 0.0, 0.0)
                for _ in texts
            ),
        )


class FakeRepository:
    def __init__(self) -> None:
        self.stored = 0
        self.processing_run_id: UUID | None = None

    async def pending_chunks(
        self,
        *,
        processing_run_id: UUID,
        provider: str,
        model: str,
        limit: int,
    ) -> tuple[ChunkForEmbedding, ...]:
        self.processing_run_id = processing_run_id

        return (
            ChunkForEmbedding(
                chunk_id=UUID(
                    "018f0000-0000-7000-8000-000000000001"
                ),
                content="knowledge graph drug discovery",
            ),
        )

    async def store_embeddings(
        self,
        *,
        chunks: Sequence[ChunkForEmbedding],
        batch: EmbeddingBatch,
    ) -> int:
        self.stored = len(batch.vectors)
        return self.stored

    async def lexical_search(
        self,
        **_: object,
    ) -> tuple[RetrievalHit, ...]:
        return ()

    async def vector_search(
        self,
        **_: object,
    ) -> tuple[RetrievalHit, ...]:
        return ()


@pytest.mark.asyncio
async def test_embedding_service_embeds_pending_chunks() -> None:
    repository = FakeRepository()

    service = EmbeddingService(
        repository=repository,
        provider=FakeProvider(),
    )

    inserted = await service.embed_pending(
        processing_run_id=PROCESSING_RUN_ID,
    )

    assert inserted == 1
    assert repository.stored == 1
    assert repository.processing_run_id == PROCESSING_RUN_ID