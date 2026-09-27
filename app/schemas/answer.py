from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.agents.workflow import GovernedAnswerResult
from app.generation.models import GroundedAnswer, GroundingVerification
from app.governance.risk import RiskAssessment, RiskTier


class AnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=4000)
    processing_run_id: UUID
    risk_tier: RiskTier = RiskTier.STANDARD


class AnswerResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    workflow_id: UUID
    processing_run_id: UUID
    provider: str
    model: str
    retrieved_evidence_count: int
    final_answer: GroundedAnswer
    verification: GroundingVerification
    risk: RiskAssessment
    review_id: UUID | None

    @classmethod
    def from_result(cls, result: GovernedAnswerResult) -> AnswerResponse:
        return cls(
            workflow_id=result.workflow_id,
            processing_run_id=result.processing_run_id,
            provider=result.provider,
            model=result.model,
            retrieved_evidence_count=len(result.retrieval_hits),
            final_answer=result.final_answer,
            verification=result.verification,
            risk=result.risk,
            review_id=result.review_id,
        )
