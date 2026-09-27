from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.agents.workflow import GovernedAnswerResult
from app.api.dependencies import get_answer_workflow
from app.generation.models import Citation, GroundedAnswer, GroundingVerification
from app.governance.risk import RiskAssessment, RiskDisposition
from app.main import app
from app.retrieval.models import RetrievalHit

RUN_ID = UUID("018f0000-0000-7000-8000-000000000100")
DOCUMENT_ID = UUID("018f0000-0000-7000-8000-000000000200")
CHUNK_ID = UUID("018f0000-0000-7000-8000-000000000300")


class FakeWorkflow:
    async def answer(self, **_: object) -> GovernedAnswerResult:
        answer = GroundedAnswer(
            answer="Grounded answer.",
            citations=(Citation(chunk_id=CHUNK_ID),),
        )
        return GovernedAnswerResult(
            workflow_id=uuid4(),
            processing_run_id=RUN_ID,
            provider="fake",
            model="deterministic",
            retrieval_hits=(
                RetrievalHit(
                    chunk_id=CHUNK_ID,
                    document_id=DOCUMENT_ID,
                    content="Sensitive evidence is not returned by the answer endpoint.",
                    score=0.9,
                ),
            ),
            candidate_answer=answer,
            verification=GroundingVerification(valid=True),
            risk=RiskAssessment(
                disposition=RiskDisposition.ALLOW,
                reason="grounding policy passed",
            ),
            final_answer=answer,
        )


def test_answer_endpoint_returns_governed_result_without_evidence_text() -> None:
    app.dependency_overrides[get_answer_workflow] = lambda: FakeWorkflow()
    try:
        response = TestClient(app).post(
            "/api/answer",
            json={
                "query": "What does the evidence say?",
                "processing_run_id": str(RUN_ID),
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["retrieved_evidence_count"] == 1
    assert payload["risk"]["disposition"] == "allow"
    assert "retrieval_hits" not in payload
    assert "candidate_answer" not in payload
