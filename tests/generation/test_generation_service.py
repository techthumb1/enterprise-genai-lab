from uuid import UUID

import pytest

from app.generation.models import (
    Citation,
    EvidenceChunk,
    GenerationRequest,
    GroundedAnswer,
)
from app.generation.service import GenerationService

PROCESSING_RUN_ID = UUID(
    "018f0000-0000-7000-8000-000000000100"
)
DOCUMENT_ID = UUID(
    "018f0000-0000-7000-8000-000000000200"
)
CHUNK_ID = UUID(
    "018f0000-0000-7000-8000-000000000300"
)
UNKNOWN_CHUNK_ID = UUID(
    "018f0000-0000-7000-8000-000000000999"
)


class FakeProvider:
    provider = "fake"
    model = "deterministic"

    def __init__(
        self,
        answer: GroundedAnswer,
    ) -> None:
        self.answer = answer
        self.calls = 0

    async def generate(
        self,
        request: GenerationRequest,
    ) -> GroundedAnswer:
        self.calls += 1
        return self.answer


class FailingProvider:
    provider = "fake"
    model = "failing"

    async def generate(
        self,
        request: GenerationRequest,
    ) -> GroundedAnswer:
        raise RuntimeError("provider unavailable")


def make_request() -> GenerationRequest:
    return GenerationRequest(
        query="What does the evidence say?",
        processing_run_id=PROCESSING_RUN_ID,
        evidence=(
            EvidenceChunk(
                chunk_id=CHUNK_ID,
                document_id=DOCUMENT_ID,
                processing_run_id=PROCESSING_RUN_ID,
                content="Grounded evidence.",
            ),
        ),
    )


async def test_valid_answer_is_released() -> None:
    provider = FakeProvider(
        GroundedAnswer(
            answer="Grounded response.",
            citations=(
                Citation(chunk_id=CHUNK_ID),
            ),
        )
    )

    service = GenerationService(
        provider=provider,
    )

    result = await service.generate(
        make_request()
    )

    assert result.verification.valid is True
    assert result.final_answer.abstained is False
    assert result.candidate_answer == result.final_answer


async def test_invalid_citation_forces_abstention() -> None:
    provider = FakeProvider(
        GroundedAnswer(
            answer="Unsupported response.",
            citations=(
                Citation(
                    chunk_id=UNKNOWN_CHUNK_ID
                ),
            ),
        )
    )

    service = GenerationService(
        provider=provider,
    )

    result = await service.generate(
        make_request()
    )

    assert result.verification.valid is False
    assert result.candidate_answer is not None
    assert result.candidate_answer.abstained is False
    assert result.final_answer.abstained is True
    assert (
        result.final_answer.abstention_reason
        == "grounding verification failed"
    )


async def test_no_evidence_abstains_without_provider_call() -> None:
    provider = FakeProvider(
        GroundedAnswer(
            answer="Should never be generated.",
        )
    )

    service = GenerationService(
        provider=provider,
    )

    request = GenerationRequest(
        query="What does the evidence say?",
        processing_run_id=PROCESSING_RUN_ID,
    )

    result = await service.generate(request)

    assert provider.calls == 0
    assert result.candidate_answer is None
    assert result.final_answer.abstained is True
    assert result.verification.valid is True


async def test_provider_abstention_is_preserved() -> None:
    provider = FakeProvider(
        GroundedAnswer(
            abstained=True,
            abstention_reason="insufficient support",
        )
    )

    service = GenerationService(
        provider=provider,
    )

    result = await service.generate(
        make_request()
    )

    assert result.verification.valid is True
    assert result.final_answer.abstained is True
    assert (
        result.final_answer.abstention_reason
        == "insufficient support"
    )


async def test_provider_failure_is_not_mislabeled_as_abstention() -> None:
    service = GenerationService(
        provider=FailingProvider(),
    )

    with pytest.raises(
        RuntimeError,
        match="provider unavailable",
    ):
        await service.generate(
            make_request()
        )