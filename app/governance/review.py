from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.generation.models import EvidenceChunk, GroundedAnswer


class ReviewStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ReviewRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    workflow_id: UUID
    status: ReviewStatus
    reason: str
    candidate_answer: GroundedAnswer
    evidence: tuple[EvidenceChunk, ...]
    reviewer_id: str | None = None
    reviewer_comment: str | None = None
    created_at: datetime
    decided_at: datetime | None = None


class ReviewDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: ReviewStatus
    reviewer_id: str = Field(min_length=1, max_length=255)
    comment: str = Field(min_length=1, max_length=4000)


class ReviewRepository(Protocol):
    async def create_pending(
        self,
        *,
        workflow_id: UUID,
        reason: str,
        candidate_answer: GroundedAnswer,
        evidence: tuple[EvidenceChunk, ...],
    ) -> ReviewRecord: ...

    async def get(self, review_id: UUID) -> ReviewRecord | None: ...

    async def decide(
        self,
        *,
        review_id: UUID,
        decision: ReviewDecision,
    ) -> ReviewRecord | None: ...


class ReviewNotFoundError(LookupError):
    pass


class ReviewConflictError(RuntimeError):
    pass


class ReviewService:
    def __init__(self, repository: ReviewRepository) -> None:
        self._repository = repository

    async def create_pending(
        self,
        *,
        workflow_id: UUID,
        reason: str,
        candidate_answer: GroundedAnswer,
        evidence: tuple[EvidenceChunk, ...],
    ) -> ReviewRecord:
        return await self._repository.create_pending(
            workflow_id=workflow_id,
            reason=reason,
            candidate_answer=candidate_answer,
            evidence=evidence,
        )

    async def get(self, review_id: UUID) -> ReviewRecord:
        review = await self._repository.get(review_id)
        if review is None:
            raise ReviewNotFoundError(str(review_id))
        return review

    async def decide(
        self,
        *,
        review_id: UUID,
        decision: ReviewDecision,
    ) -> ReviewRecord:
        if decision.status is ReviewStatus.PENDING:
            raise ValueError("a decision must approve or reject the review")
        existing = await self._repository.get(review_id)
        if existing is None:
            raise ReviewNotFoundError(str(review_id))
        if existing.status is not ReviewStatus.PENDING:
            raise ReviewConflictError("review has already been decided")
        decided = await self._repository.decide(
            review_id=review_id,
            decision=decision,
        )
        if decided is None:
            raise ReviewConflictError("review was decided concurrently")
        return decided
