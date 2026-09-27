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
        candidate = await self.generate_candidate(request)
        return self.govern(request=request, candidate=candidate)

    @property
    def provider(self) -> str:
        return self._provider.provider

    @property
    def model(self) -> str:
        return self._provider.model

    async def generate_candidate(
        self,
        request: GenerationRequest,
    ) -> GroundedAnswer | None:
        """Generate a candidate without deciding whether it may be released."""
        if not request.evidence:
            return None
        return await self._provider.generate(request)

    def govern(
        self,
        *,
        request: GenerationRequest,
        candidate: GroundedAnswer | None,
    ) -> GenerationResult:
        """Apply deterministic citation policy to a candidate answer."""
        if candidate is None:
            abstention = GroundedAnswer(
                abstained=True,
                abstention_reason="no retrieval evidence was available",
            )
            return GenerationResult(
                provider=self.provider,
                model=self.model,
                candidate_answer=None,
                final_answer=abstention,
                verification=GroundingVerification(valid=True),
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
            provider=self.provider,
            model=self.model,
            candidate_answer=candidate,
            final_answer=final_answer,
            verification=verification,
        )
