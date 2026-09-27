from __future__ import annotations

from uuid import UUID

from app.retrieval.embeddings import EmbeddingProvider
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.models import RetrievalHit
from app.retrieval.repository import RetrievalRepository


class RetrievalService:
    def __init__(
        self,
        *,
        repository: RetrievalRepository,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self._repository = repository
        self._embedding_provider = embedding_provider

    async def lexical_search(
        self,
        *,
        processing_run_id: UUID,
        query: str,
        limit: int = 5,
    ) -> tuple[RetrievalHit, ...]:
        if not query.strip():
            raise ValueError("query must not be empty")

        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        return await self._repository.lexical_search(
            processing_run_id=processing_run_id,
            query=query,
            limit=limit,
        )

    async def vector_search(
        self,
        *,
        processing_run_id: UUID,
        query: str,
        limit: int = 5,
    ) -> tuple[RetrievalHit, ...]:
        if not query.strip():
            raise ValueError("query must not be empty")

        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        batch = await self._embedding_provider.embed([query])

        if len(batch.vectors) != 1:
            raise RuntimeError(
                "query embedding must contain exactly one vector"
            )

        return await self._repository.vector_search(
            processing_run_id=processing_run_id,
            vector=batch.vectors[0],
            provider=batch.provider,
            model=batch.model,
            dimensions=batch.dimensions,
            limit=limit,
        )

    async def hybrid_search(
        self,
        *,
        processing_run_id: UUID,
        query: str,
        limit: int = 5,
        candidate_limit: int = 20,
        rrf_k: int = 60,
    ) -> tuple[RetrievalHit, ...]:
        if not query.strip():
            raise ValueError("query must not be empty")

        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        if candidate_limit <= 0:
            raise ValueError(
                "candidate_limit must be greater than zero"
            )

        if candidate_limit < limit:
            raise ValueError(
                "candidate_limit must be greater than or equal to limit"
            )

        lexical = await self.lexical_search(
            processing_run_id=processing_run_id,
            query=query,
            limit=candidate_limit,
        )

        vector = await self.vector_search(
            processing_run_id=processing_run_id,
            query=query,
            limit=candidate_limit,
        )

        return reciprocal_rank_fusion(
            rankings=(lexical, vector),
            k=rrf_k,
            limit=limit,
        )