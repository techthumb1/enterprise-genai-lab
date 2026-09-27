from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.generation.models import GroundedAnswer
from app.governance.review import (
    ReviewConflictError,
    ReviewDecision,
    ReviewRecord,
    ReviewService,
    ReviewStatus,
)


class MemoryReviewRepository:
    def __init__(self) -> None:
        self.record: ReviewRecord | None = None

    async def create_pending(self, **kwargs: object) -> ReviewRecord:
        raise NotImplementedError

    async def get(self, review_id: UUID) -> ReviewRecord | None:
        return self.record if self.record and self.record.id == review_id else None

    async def list(
        self,
        *,
        status: ReviewStatus | None,
        limit: int,
    ) -> tuple[ReviewRecord, ...]:
        if self.record is None or (
            status is not None and self.record.status is not status
        ):
            return ()
        return (self.record,)[:limit]

    async def decide(
        self, *, review_id: UUID, decision: ReviewDecision
    ) -> ReviewRecord | None:
        if self.record is None or self.record.status is not ReviewStatus.PENDING:
            return None
        self.record = self.record.model_copy(
            update={
                "status": decision.status,
                "reviewer_id": decision.reviewer_id,
                "reviewer_comment": decision.comment,
                "decided_at": datetime.now(UTC),
            }
        )
        return self.record


async def test_review_can_be_approved_once() -> None:
    repository = MemoryReviewRepository()
    repository.record = ReviewRecord(
        id=uuid4(),
        workflow_id=uuid4(),
        status=ReviewStatus.PENDING,
        reason="high risk",
        candidate_answer=GroundedAnswer(answer="Candidate", citations=()),
        evidence=(),
        created_at=datetime.now(UTC),
    )
    service = ReviewService(repository)
    decision = ReviewDecision(
        status=ReviewStatus.APPROVED,
        reviewer_id="reviewer-1",
        comment="Evidence supports release.",
    )

    result = await service.decide(review_id=repository.record.id, decision=decision)
    assert result.status is ReviewStatus.APPROVED

    with pytest.raises(ReviewConflictError):
        await service.decide(review_id=result.id, decision=decision)


async def test_review_service_lists_pending_reviews() -> None:
    repository = MemoryReviewRepository()
    repository.record = ReviewRecord(
        id=uuid4(),
        workflow_id=uuid4(),
        status=ReviewStatus.PENDING,
        reason="high risk",
        candidate_answer=GroundedAnswer(answer="Candidate", citations=()),
        evidence=(),
        created_at=datetime.now(UTC),
    )

    reviews = await ReviewService(repository).list()

    assert reviews == (repository.record,)
