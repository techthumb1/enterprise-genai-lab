from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EvaluationModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class SourceSpan(EvaluationModel):
    start_char: int = Field(ge=0)
    end_char: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_bounds(self) -> SourceSpan:
        if self.end_char <= self.start_char:
            raise ValueError(
                "end_char must be greater than start_char"
            )

        return self


class ChunkSpan(EvaluationModel):
    chunk_id: UUID
    source_span: SourceSpan


class LabeledQuery(EvaluationModel):
    name: str = Field(min_length=1)
    query: str = Field(min_length=1)
    relevant_spans: tuple[SourceSpan, ...] = Field(
        min_length=1
    )


def spans_overlap(
    left: SourceSpan,
    right: SourceSpan,
) -> bool:
    return (
        left.start_char < right.end_char
        and right.start_char < left.end_char
    )


def relevant_chunk_ids(
    *,
    chunks: Sequence[ChunkSpan],
    relevant_spans: Sequence[SourceSpan],
) -> set[UUID]:
    return {
        chunk.chunk_id
        for chunk in chunks
        if any(
            spans_overlap(
                chunk.source_span,
                relevant_span,
            )
            for relevant_span in relevant_spans
        )
    }

class RetrievalMetrics(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    recall_at_k: float = Field(ge=0.0, le=1.0)
    reciprocal_rank: float = Field(ge=0.0, le=1.0)


def evaluate_ranking(
    *,
    retrieved: Sequence[UUID],
    relevant: set[UUID],
    k: int,
) -> RetrievalMetrics:
    if k <= 0:
        raise ValueError("k must be greater than zero")

    if not relevant:
        raise ValueError("relevant must not be empty")

    top_k = retrieved[:k]

    relevant_retrieved = relevant.intersection(top_k)

    recall = len(relevant_retrieved) / len(relevant)

    reciprocal_rank = 0.0

    for rank, chunk_id in enumerate(retrieved, start=1):
        if chunk_id in relevant:
            reciprocal_rank = 1.0 / rank
            break

    return RetrievalMetrics(
        recall_at_k=recall,
        reciprocal_rank=reciprocal_rank,
    )