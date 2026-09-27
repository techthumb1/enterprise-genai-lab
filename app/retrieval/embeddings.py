from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from app.retrieval.models import EmbeddingBatch


class EmbeddingProvider(Protocol):
    provider: str
    model: str

    async def embed(
        self,
        texts: Sequence[str],
    ) -> EmbeddingBatch:
        ...