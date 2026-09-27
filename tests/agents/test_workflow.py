from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.agents.workflow import GovernedAnswerWorkflow
from app.generation.models import Citation, EvidenceChunk, GenerationRequest, GroundedAnswer
from app.generation.service import GenerationService
from app.governance.review import ReviewRecord, ReviewStatus
from app.governance.risk import RiskDisposition, RiskTier
from app.retrieval.models import RetrievalHit

PROCESSING_RUN_ID = UUID("018f0000-0000-7000-8000-000000000100")
DOCUMENT_ID = UUID("018f0000-0000-7000-8000-000000000200")
CHUNK_ID = UUID("018f0000-0000-7000-8000-000000000300")
UNKNOWN_CHUNK_ID = UUID("018f0000-0000-7000-8000-000000000999")


class FakeRetriever:
    def __init__(self, hits: tuple[RetrievalHit, ...]) -> None:
        self.hits = hits

    async def vector_search(
        self,
        *,
        processing_run_id: UUID,
        query: str,
        limit: int = 5,
    ) -> tuple[RetrievalHit, ...]:
        return self.hits[:limit]


class FakeProvider:
    provider = "fake"
    model = "deterministic"

    def __init__(self, answer: GroundedAnswer) -> None:
        self.answer = answer

    async def generate(self, request: GenerationRequest) -> GroundedAnswer:
        return self.answer


class MemoryReviewService:
    async def create_pending(
        self,
        *,
        workflow_id: UUID,
        reason: str,
        candidate_answer: GroundedAnswer,
        evidence: tuple[EvidenceChunk, ...],
    ) -> ReviewRecord:
        return ReviewRecord(
            id=uuid4(),
            workflow_id=workflow_id,
            status=ReviewStatus.PENDING,
            reason=reason,
            candidate_answer=candidate_answer,
            evidence=(),
            created_at=datetime.now(UTC),
        )


def hit() -> RetrievalHit:
    return RetrievalHit(
        chunk_id=CHUNK_ID,
        document_id=DOCUMENT_ID,
        content="The graph is converted for compatible learning algorithms.",
        score=0.9,
    )


async def test_workflow_releases_verified_standard_answer() -> None:
    workflow = GovernedAnswerWorkflow(
        retrieval=FakeRetriever((hit(),)),
        generation=GenerationService(
            provider=FakeProvider(
                GroundedAnswer(
                    answer="It enables compatible algorithms.",
                    citations=(Citation(chunk_id=CHUNK_ID),),
                )
            )
        ),
    )
    result = await workflow.answer(
        query="Why convert the graph?",
        processing_run_id=PROCESSING_RUN_ID,
    )
    assert result.risk.disposition is RiskDisposition.ALLOW
    assert result.final_answer.abstained is False


async def test_workflow_abstains_on_fabricated_citation() -> None:
    workflow = GovernedAnswerWorkflow(
        retrieval=FakeRetriever((hit(),)),
        generation=GenerationService(
            provider=FakeProvider(
                GroundedAnswer(
                    answer="Unsupported.",
                    citations=(Citation(chunk_id=UNKNOWN_CHUNK_ID),),
                )
            )
        ),
    )
    result = await workflow.answer(
        query="Why convert the graph?",
        processing_run_id=PROCESSING_RUN_ID,
    )
    assert result.risk.disposition is RiskDisposition.ABSTAIN
    assert result.candidate_answer is not None
    assert result.final_answer.abstained is True


async def test_workflow_persists_high_risk_review() -> None:
    workflow = GovernedAnswerWorkflow(
        retrieval=FakeRetriever((hit(),)),
        generation=GenerationService(
            provider=FakeProvider(
                GroundedAnswer(
                    answer="Candidate.",
                    citations=(Citation(chunk_id=CHUNK_ID),),
                )
            )
        ),
        review_service=MemoryReviewService(),
    )
    result = await workflow.answer(
        query="Why convert the graph?",
        processing_run_id=PROCESSING_RUN_ID,
        risk_tier=RiskTier.HIGH,
    )
    assert result.risk.disposition is RiskDisposition.HUMAN_REVIEW
    assert result.review_id is not None
    assert result.final_answer.abstained is True
