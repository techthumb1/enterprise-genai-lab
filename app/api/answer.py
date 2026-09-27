from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import WorkflowDependency
from app.generation.provider import GenerationOutputError, GenerationProviderError
from app.schemas.answer import AnswerRequest, AnswerResponse

router = APIRouter(prefix="/api", tags=["governed answers"])


@router.post("/answer", response_model=AnswerResponse)
async def answer(
    request: AnswerRequest,
    workflow: WorkflowDependency,
) -> AnswerResponse:
    try:
        result = await workflow.answer(
            query=request.query,
            processing_run_id=request.processing_run_id,
            risk_tier=request.risk_tier,
        )
    except GenerationProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="generation provider is temporarily unavailable",
        ) from exc
    except GenerationOutputError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="generation provider returned an invalid response",
        ) from exc
    return AnswerResponse.from_result(result)
