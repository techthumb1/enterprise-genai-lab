from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal, Protocol
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

    status: Literal[ReviewStatus.APPROVED, ReviewStatus.REJECTED]
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

    async def list(
        self,
        *,
        status: ReviewStatus | None,
        limit: int,
    ) -> tuple[ReviewRecord, ...]: ...

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

    async def list(
        self,
        *,
        status: ReviewStatus | None = ReviewStatus.PENDING,
        limit: int = 50,
    ) -> tuple[ReviewRecord, ...]:
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        return await self._repository.list(status=status, limit=limit)

    async def decide(
        self,
        *,
        review_id: UUID,
        decision: ReviewDecision,
    ) -> ReviewRecord:
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
