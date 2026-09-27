from __future__ import annotations

import logging
from time import perf_counter
from typing import Any, Protocol, TypedDict, cast
from uuid import UUID, uuid4

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, ConfigDict

from app.generation.context import assemble_generation_request
from app.generation.models import (
    EvidenceChunk,
    GenerationRequest,
    GroundedAnswer,
    GroundingVerification,
)
from app.generation.service import GenerationService
from app.generation.verification import verify_grounding
from app.governance.review import ReviewRecord
from app.governance.risk import (
    RiskAssessment,
    RiskDisposition,
    RiskTier,
    assess_risk,
)
from app.retrieval.models import RetrievalHit

logger = logging.getLogger(__name__)


class VectorRetriever(Protocol):
    async def vector_search(
        self,
        *,
        processing_run_id: UUID,
        query: str,
        limit: int = 5,
    ) -> tuple[RetrievalHit, ...]: ...


class PendingReviewService(Protocol):
    async def create_pending(
        self,
        *,
        workflow_id: UUID,
        reason: str,
        candidate_answer: GroundedAnswer,
        evidence: tuple[EvidenceChunk, ...],
    ) -> ReviewRecord: ...


class WorkflowState(TypedDict, total=False):
    workflow_id: UUID
    query: str
    processing_run_id: UUID
    risk_tier: RiskTier
    retrieval_hits: tuple[RetrievalHit, ...]
    generation_request: GenerationRequest
    candidate_answer: GroundedAnswer | None
    verification: GroundingVerification
    risk: RiskAssessment
    final_answer: GroundedAnswer
    review_id: UUID | None


class GovernedAnswerResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    workflow_id: UUID
    processing_run_id: UUID
    provider: str
    model: str
    retrieval_hits: tuple[RetrievalHit, ...]
    candidate_answer: GroundedAnswer | None
    verification: GroundingVerification
    risk: RiskAssessment
    final_answer: GroundedAnswer
    review_id: UUID | None = None


class GovernedAnswerWorkflow:
    """LangGraph orchestration over independently testable domain primitives."""

    def __init__(
        self,
        *,
        retrieval: VectorRetriever,
        generation: GenerationService,
        review_service: PendingReviewService | None = None,
        retrieval_limit: int = 5,
    ) -> None:
        if retrieval_limit <= 0:
            raise ValueError("retrieval_limit must be greater than zero")
        self._retrieval = retrieval
        self._generation = generation
        self._review_service = review_service
        self._retrieval_limit = retrieval_limit
        self._graph = self._build_graph()

    def _build_graph(self) -> Any:
        builder = StateGraph(WorkflowState)
        builder.add_node("retrieve", self._retrieve)
        builder.add_node("assemble_context", self._assemble_context)
        builder.add_node("generate", self._generate)
        builder.add_node("verify_grounding", self._verify_grounding)
        builder.add_node("risk_gate", self._risk_gate)
        builder.add_node("finalize", self._finalize)
        builder.add_node("abstain", self._abstain)
        builder.add_node("human_review", self._human_review)
        builder.add_edge(START, "retrieve")
        builder.add_edge("retrieve", "assemble_context")
        builder.add_edge("assemble_context", "generate")
        builder.add_edge("generate", "verify_grounding")
        builder.add_edge("verify_grounding", "risk_gate")
        builder.add_conditional_edges(
            "risk_gate",
            self._route,
            {
                RiskDisposition.ALLOW.value: "finalize",
                RiskDisposition.ABSTAIN.value: "abstain",
                RiskDisposition.HUMAN_REVIEW.value: "human_review",
            },
        )
        builder.add_edge("finalize", END)
        builder.add_edge("abstain", END)
        builder.add_edge("human_review", END)
        return builder.compile()

    async def _retrieve(self, state: WorkflowState) -> WorkflowState:
        started = perf_counter()
        hits = await self._retrieval.vector_search(
            processing_run_id=state["processing_run_id"],
            query=state["query"],
            limit=self._retrieval_limit,
        )
        logger.info(
            "workflow retrieval completed",
            extra={
                "workflow_id": str(state["workflow_id"]),
                "processing_run_id": str(state["processing_run_id"]),
                "retrieval_mode": "vector",
                "retrieval_result_count": len(hits),
                "duration_ms": round((perf_counter() - started) * 1000, 2),
            },
        )
        return {"retrieval_hits": hits}

    async def _assemble_context(self, state: WorkflowState) -> WorkflowState:
        request = assemble_generation_request(
            query=state["query"],
            processing_run_id=state["processing_run_id"],
            hits=state["retrieval_hits"],
        )
        return {"generation_request": request}

    async def _generate(self, state: WorkflowState) -> WorkflowState:
        started = perf_counter()
        candidate = await self._generation.generate_candidate(
            state["generation_request"]
        )
        logger.info(
            "workflow generation completed",
            extra={
                "workflow_id": str(state["workflow_id"]),
                "provider": self._generation.provider,
                "model": self._generation.model,
                "provider_abstained": candidate.abstained if candidate else None,
                "duration_ms": round((perf_counter() - started) * 1000, 2),
            },
        )
        return {"candidate_answer": candidate}

    async def _verify_grounding(self, state: WorkflowState) -> WorkflowState:
        candidate = state["candidate_answer"]
        verification = (
            GroundingVerification(valid=True)
            if candidate is None
            else verify_grounding(
                request=state["generation_request"],
                answer=candidate,
            )
        )
        return {"verification": verification}

    async def _risk_gate(self, state: WorkflowState) -> WorkflowState:
        risk = assess_risk(
            has_evidence=bool(state["generation_request"].evidence),
            candidate=state["candidate_answer"],
            verification=state["verification"],
            risk_tier=state["risk_tier"],
        )
        logger.info(
            "workflow risk decision completed",
            extra={
                "workflow_id": str(state["workflow_id"]),
                "grounding_valid": state["verification"].valid,
                "risk_tier": state["risk_tier"].value,
                "risk_disposition": risk.disposition.value,
            },
        )
        return {"risk": risk}

    def _route(self, state: WorkflowState) -> str:
        return state["risk"].disposition.value

    async def _finalize(self, state: WorkflowState) -> WorkflowState:
        candidate = state["candidate_answer"]
        if candidate is None:
            raise RuntimeError("allow decision requires a candidate answer")
        return {"final_answer": candidate, "review_id": None}

    async def _abstain(self, state: WorkflowState) -> WorkflowState:
        candidate = state["candidate_answer"]
        final_answer = (
            candidate
            if candidate is not None and candidate.abstained
            else GroundedAnswer(
                abstained=True,
                abstention_reason=state["risk"].reason,
            )
        )
        return {"final_answer": final_answer, "review_id": None}

    async def _human_review(self, state: WorkflowState) -> WorkflowState:
        candidate = state["candidate_answer"]
        if candidate is None:
            raise RuntimeError("human review requires a candidate answer")
        if self._review_service is None:
            raise RuntimeError("human review persistence is not configured")
        review = await self._review_service.create_pending(
            workflow_id=state["workflow_id"],
            reason=state["risk"].reason,
            candidate_answer=candidate,
            evidence=state["generation_request"].evidence,
        )
        return {
            "final_answer": GroundedAnswer(
                abstained=True,
                abstention_reason="answer is pending human review",
            ),
            "review_id": review.id,
        }

    async def answer(
        self,
        *,
        query: str,
        processing_run_id: UUID,
        risk_tier: RiskTier = RiskTier.STANDARD,
        workflow_id: UUID | None = None,
    ) -> GovernedAnswerResult:
        initial: WorkflowState = {
            "workflow_id": workflow_id or uuid4(),
            "query": query,
            "processing_run_id": processing_run_id,
            "risk_tier": risk_tier,
        }
        state = cast(WorkflowState, await self._graph.ainvoke(initial))
        return GovernedAnswerResult(
            workflow_id=state["workflow_id"],
            processing_run_id=state["processing_run_id"],
            provider=self._generation.provider,
            model=self._generation.model,
            retrieval_hits=state["retrieval_hits"],
            candidate_answer=state["candidate_answer"],
            verification=state["verification"],
            risk=state["risk"],
            final_answer=state["final_answer"],
            review_id=state["review_id"],
        )
