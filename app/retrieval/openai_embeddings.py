from __future__ import annotations

from collections.abc import Sequence

from openai import AsyncOpenAI

from app.retrieval.models import EmbeddingBatch


class OpenAIEmbeddingProvider:
    provider = "openai"

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "text-embedding-3-small",
    ) -> None:
        self.model = model
        self._client = AsyncOpenAI(api_key=api_key)

    async def embed(
        self,
        texts: Sequence[str],
    ) -> EmbeddingBatch:
        if not texts:
            raise ValueError("texts must not be empty")

        response = await self._client.embeddings.create(
            model=self.model,
            input=list(texts),
            encoding_format="float",
        )

        ordered = sorted(
            response.data,
            key=lambda item: item.index,
        )

        vectors = tuple(
            tuple(float(value) for value in item.embedding)
            for item in ordered
        )

        if len(vectors) != len(texts):
            raise RuntimeError(
                "embedding provider returned unexpected vector count"
            )

        dimensions = len(vectors[0])

        return EmbeddingBatch(
            provider=self.provider,
            model=self.model,
            dimensions=dimensions,
            vectors=vectors,
        )