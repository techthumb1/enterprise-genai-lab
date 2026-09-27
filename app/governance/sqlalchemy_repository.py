from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.generation.models import EvidenceChunk, GroundedAnswer
from app.governance.review import ReviewDecision, ReviewRecord, ReviewStatus
from app.models.review import HumanReview


def _to_record(row: HumanReview) -> ReviewRecord:
    return ReviewRecord(
        id=row.id,
        workflow_id=row.workflow_id,
        status=ReviewStatus(row.status),
        reason=row.reason,
        candidate_answer=GroundedAnswer.model_validate(row.candidate_answer),
        evidence=tuple(EvidenceChunk.model_validate(item) for item in row.evidence),
        reviewer_id=row.reviewer_id,
        reviewer_comment=row.reviewer_comment,
        created_at=row.created_at,
        decided_at=row.decided_at,
    )


class SQLAlchemyReviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_pending(
        self,
        *,
        workflow_id: UUID,
        reason: str,
        candidate_answer: GroundedAnswer,
        evidence: tuple[EvidenceChunk, ...],
    ) -> ReviewRecord:
        row = HumanReview(
            workflow_id=workflow_id,
            status=ReviewStatus.PENDING.value,
            reason=reason,
            candidate_answer=candidate_answer.model_dump(mode="json"),
            evidence=[item.model_dump(mode="json") for item in evidence],
        )
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return _to_record(row)

    async def get(self, review_id: UUID) -> ReviewRecord | None:
        row = await self._session.scalar(
            select(HumanReview).where(HumanReview.id == review_id)
        )
        return None if row is None else _to_record(row)

    async def list(
        self,
        *,
        status: ReviewStatus | None,
        limit: int,
    ) -> tuple[ReviewRecord, ...]:
        statement = select(HumanReview).order_by(
            HumanReview.created_at.desc(),
            HumanReview.id.desc(),
        )
        if status is not None:
            statement = statement.where(HumanReview.status == status.value)
        rows = await self._session.scalars(statement.limit(limit))
        return tuple(_to_record(row) for row in rows)

    async def decide(
        self,
        *,
        review_id: UUID,
        decision: ReviewDecision,
    ) -> ReviewRecord | None:
        statement = (
            update(HumanReview)
            .where(
                HumanReview.id == review_id,
                HumanReview.status == ReviewStatus.PENDING.value,
            )
            .values(
                status=decision.status.value,
                reviewer_id=decision.reviewer_id,
                reviewer_comment=decision.comment,
                decided_at=datetime.now(UTC),
            )
            .returning(HumanReview)
        )
        row = (await self._session.execute(statement)).scalar_one_or_none()
        if row is None:
            await self._session.rollback()
            return None
        await self._session.commit()
        return _to_record(row)
