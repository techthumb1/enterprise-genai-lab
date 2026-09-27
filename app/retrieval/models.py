from __future__ import annotations

from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RetrievalModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class ChunkForEmbedding(RetrievalModel):
    chunk_id: UUID
    content: str = Field(min_length=1)


class EmbeddingBatch(RetrievalModel):
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    dimensions: int = Field(gt=0)
    vectors: tuple[tuple[float, ...], ...]

    @model_validator(mode="after")
    def validate_dimensions(self) -> Self:
        if any(
            len(vector) != self.dimensions
            for vector in self.vectors
        ):
            raise ValueError(
                "all embedding vectors must match dimensions"
            )

        return self


class RetrievalHit(RetrievalModel):
    chunk_id: UUID
    document_id: UUID
    content: str
    score: float