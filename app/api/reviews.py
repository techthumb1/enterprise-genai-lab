from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import ReviewServiceDependency
from app.governance.review import (
    ReviewConflictError,
    ReviewDecision,
    ReviewNotFoundError,
    ReviewRecord,
)

router = APIRouter(prefix="/api/reviews", tags=["human review"])


@router.get("/{review_id}", response_model=ReviewRecord)
async def get_review(
    review_id: UUID,
    service: ReviewServiceDependency,
) -> ReviewRecord:
    try:
        return await service.get(review_id)
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc


@router.post("/{review_id}/decision", response_model=ReviewRecord)
async def decide_review(
    review_id: UUID,
    decision: ReviewDecision,
    service: ReviewServiceDependency,
) -> ReviewRecord:
    try:
        return await service.decide(review_id=review_id, decision=decision)
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc
    except ReviewConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="review is no longer pending",
        ) from exc
