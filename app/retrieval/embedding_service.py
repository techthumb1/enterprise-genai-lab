from __future__ import annotations

from uuid import UUID

from app.retrieval.embeddings import EmbeddingProvider
from app.retrieval.repository import RetrievalRepository


class EmbeddingService:
    def __init__(
        self,
        *,
        repository: RetrievalRepository,
        provider: EmbeddingProvider,
    ) -> None:
        self._repository = repository
        self._provider = provider

    async def embed_pending(
        self,
        *,
        processing_run_id: UUID,
        limit: int = 64,
    ) -> int:
        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        chunks = await self._repository.pending_chunks(
            processing_run_id=processing_run_id,
            provider=self._provider.provider,
            model=self._provider.model,
            limit=limit,
        )

        if not chunks:
            return 0

        batch = await self._provider.embed(
            [chunk.content for chunk in chunks]
        )

        return await self._repository.store_embeddings(
            chunks=chunks,
            batch=batch,
        )