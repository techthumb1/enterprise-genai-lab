from __future__ import annotations

from app.generation.models import (
    GenerationRequest,
    GenerationResult,
    GroundedAnswer,
    GroundingVerification,
)
from app.generation.provider import GenerationProvider
from app.generation.verification import verify_grounding


class GenerationService:
    def __init__(
        self,
        *,
        provider: GenerationProvider,
    ) -> None:
        self._provider = provider

    async def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResult:
        if not request.evidence:
            abstention = GroundedAnswer(
                abstained=True,
                abstention_reason=(
                    "no retrieval evidence was available"
                ),
            )

            return GenerationResult(
                provider=self._provider.provider,
                model=self._provider.model,
                candidate_answer=None,
                final_answer=abstention,
                verification=GroundingVerification(
                    valid=True,
                ),
            )

        candidate = await self._provider.generate(
            request
        )

        verification = verify_grounding(
            request=request,
            answer=candidate,
        )

        if not verification.valid:
            final_answer = GroundedAnswer(
                abstained=True,
                abstention_reason=(
                    "grounding verification failed"
                ),
            )
        else:
            final_answer = candidate

        return GenerationResult(
            provider=self._provider.provider,
            model=self._provider.model,
            candidate_answer=candidate,
            final_answer=final_answer,
            verification=verification,
        )