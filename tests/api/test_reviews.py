from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from app.api.dependencies import get_review_service
from app.generation.models import Citation, EvidenceChunk, GroundedAnswer
from app.governance.review import ReviewRecord, ReviewStatus
from app.main import app

REVIEW_ID = UUID("018f0000-0000-7000-8000-000000000400")
WORKFLOW_ID = UUID("018f0000-0000-7000-8000-000000000500")
RUN_ID = UUID("018f0000-0000-7000-8000-000000000100")
DOCUMENT_ID = UUID("018f0000-0000-7000-8000-000000000200")
CHUNK_ID = UUID("018f0000-0000-7000-8000-000000000300")


class FakeReviewService:
    async def list(
        self,
        *,
        status: ReviewStatus | None,
        limit: int,
    ) -> tuple[ReviewRecord, ...]:
        assert status is ReviewStatus.PENDING
        assert limit == 50
        return (
            ReviewRecord(
                id=REVIEW_ID,
                workflow_id=WORKFLOW_ID,
                status=ReviewStatus.PENDING,
                reason="high-risk workflows require human approval",
                candidate_answer=GroundedAnswer(
                    answer="The policy requires approval.",
                    citations=(Citation(chunk_id=CHUNK_ID),),
                ),
                evidence=(
                    EvidenceChunk(
                        chunk_id=CHUNK_ID,
                        document_id=DOCUMENT_ID,
                        processing_run_id=RUN_ID,
                        content="High-risk outputs require reviewer approval.",
                    ),
                ),
                created_at=datetime(2026, 9, 26, 18, 30, tzinfo=UTC),
            ),
        )


def test_review_decision_rejects_pending_as_an_invalid_transition() -> None:
    app.dependency_overrides[get_review_service] = lambda: FakeReviewService()
    try:
        response = TestClient(app).post(
            f"/api/reviews/{REVIEW_ID}/decision",
            json={
                "status": "pending",
                "reviewer_id": "reviewer-1",
                "comment": "This is not a decision.",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_reviews_endpoint_returns_pending_queue_with_evidence() -> None:
    app.dependency_overrides[get_review_service] = lambda: FakeReviewService()
    try:
        response = TestClient(app).get("/api/reviews")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["id"] == str(REVIEW_ID)
    assert payload[0]["status"] == "pending"
    assert payload[0]["evidence"][0]["content"].startswith("High-risk outputs")
