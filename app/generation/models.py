from __future__ import annotations

from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class GenerationModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class EvidenceChunk(GenerationModel):
    chunk_id: UUID
    document_id: UUID
    processing_run_id: UUID
    content: str = Field(min_length=1)


class GenerationRequest(GenerationModel):
    query: str = Field(min_length=1)
    processing_run_id: UUID
    evidence: tuple[EvidenceChunk, ...] = ()

    @model_validator(mode="after")
    def validate_request(self) -> Self:
        if not self.query.strip():
            raise ValueError("query must not be empty")

        invalid_run_chunks = [
            chunk.chunk_id
            for chunk in self.evidence
            if chunk.processing_run_id != self.processing_run_id
        ]

        if invalid_run_chunks:
            raise ValueError(
                "all evidence must belong to the selected processing run"
            )

        chunk_ids = [
            chunk.chunk_id
            for chunk in self.evidence
        ]

        if len(set(chunk_ids)) != len(chunk_ids):
            raise ValueError(
                "evidence must not contain duplicate chunk IDs"
            )

        return self


class Citation(GenerationModel):
    chunk_id: UUID


class GroundedAnswer(GenerationModel):
    answer: str = ""
    citations: tuple[Citation, ...] = ()
    abstained: bool = False
    abstention_reason: str | None = None

    @model_validator(mode="after")
    def validate_answer(self) -> Self:
        if self.abstained:
            if self.answer.strip():
                raise ValueError(
                    "abstained answers cannot contain answer text"
                )

            if self.citations:
                raise ValueError(
                    "abstained answers cannot contain citations"
                )

            if (
                self.abstention_reason is None
                or not self.abstention_reason.strip()
            ):
                raise ValueError(
                    "abstained answers require an abstention reason"
                )

            return self

        if not self.answer.strip():
            raise ValueError(
                "non-abstained answers require answer text"
            )

        if self.abstention_reason is not None:
            raise ValueError(
                "non-abstained answers cannot have an abstention reason"
            )

        return self


class GroundingVerification(GenerationModel):
    valid: bool
    errors: tuple[str, ...] = ()


class GenerationResult(GenerationModel):
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    candidate_answer: GroundedAnswer | None
    final_answer: GroundedAnswer
    verification: GroundingVerification