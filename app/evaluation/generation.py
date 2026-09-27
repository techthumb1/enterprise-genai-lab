from __future__ import annotations

from collections.abc import Sequence
from time import perf_counter

from pydantic import BaseModel, ConfigDict, Field

from app.generation.models import GenerationRequest
from app.generation.provider import (
    GenerationOutputError,
    GenerationProvider,
    GenerationProviderError,
)
from app.generation.service import GenerationService


class GenerationEvaluationCase(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    case_id: str = Field(min_length=1)
    request: GenerationRequest
    expect_abstention: bool = False


class GenerationCaseResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    case_id: str
    structured_output: bool
    grounding_valid: bool
    abstained: bool
    abstention_expected: bool
    citation_count: int
    latency_ms: float
    operational_error: bool = False


class GenerationEvaluationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: str
    model: str
    cases: tuple[GenerationCaseResult, ...]
    structured_output_rate: float
    grounding_pass_rate: float
    abstention_accuracy: float
    operational_error_rate: float
    mean_latency_ms: float


async def evaluate_generation(
    *,
    provider: GenerationProvider,
    cases: Sequence[GenerationEvaluationCase],
) -> GenerationEvaluationReport:
    if not cases:
        raise ValueError("at least one evaluation case is required")
    service = GenerationService(provider=provider)
    results: list[GenerationCaseResult] = []

    for case in cases:
        started = perf_counter()
        try:
            result = await service.generate(case.request)
        except GenerationOutputError:
            results.append(
                GenerationCaseResult(
                    case_id=case.case_id,
                    structured_output=False,
                    grounding_valid=False,
                    abstained=False,
                    abstention_expected=case.expect_abstention,
                    citation_count=0,
                    latency_ms=(perf_counter() - started) * 1000,
                )
            )
            continue
        except GenerationProviderError:
            results.append(
                GenerationCaseResult(
                    case_id=case.case_id,
                    structured_output=False,
                    grounding_valid=False,
                    abstained=False,
                    abstention_expected=case.expect_abstention,
                    citation_count=0,
                    latency_ms=(perf_counter() - started) * 1000,
                    operational_error=True,
                )
            )
            continue
        results.append(
            GenerationCaseResult(
                case_id=case.case_id,
                structured_output=True,
                grounding_valid=result.verification.valid,
                abstained=result.final_answer.abstained,
                abstention_expected=case.expect_abstention,
                citation_count=len(result.final_answer.citations),
                latency_ms=(perf_counter() - started) * 1000,
            )
        )

    count = len(results)
    return GenerationEvaluationReport(
        provider=provider.provider,
        model=provider.model,
        cases=tuple(results),
        structured_output_rate=sum(item.structured_output for item in results) / count,
        grounding_pass_rate=sum(item.grounding_valid for item in results) / count,
        abstention_accuracy=sum(
            item.abstained == item.abstention_expected for item in results
        )
        / count,
        operational_error_rate=sum(item.operational_error for item in results) / count,
        mean_latency_ms=sum(item.latency_ms for item in results) / count,
    )
