from uuid import UUID

import pytest
from pydantic import ValidationError

from app.generation.models import (
    Citation,
    EvidenceChunk,
    GenerationRequest,
    GroundedAnswer,
)
from app.generation.verification import verify_grounding

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


def test_valid_grounded_answer_passes() -> None:
    request = make_request()

    answer = GroundedAnswer(
        answer="The evidence supports the answer.",
        citations=(
            Citation(chunk_id=CHUNK_ID),
        ),
    )

    result = verify_grounding(
        request=request,
        answer=answer,
    )

    assert result.valid is True
    assert result.errors == ()


def test_unknown_citation_fails() -> None:
    request = make_request()

    answer = GroundedAnswer(
        answer="Unsupported answer.",
        citations=(
            Citation(chunk_id=UNKNOWN_CHUNK_ID),
        ),
    )

    result = verify_grounding(
        request=request,
        answer=answer,
    )

    assert result.valid is False
    assert len(result.errors) == 1


def test_missing_citation_fails_for_answer() -> None:
    request = make_request()

    answer = GroundedAnswer(
        answer="Answer without evidence.",
    )

    result = verify_grounding(
        request=request,
        answer=answer,
    )

    assert result.valid is False
    assert result.errors == (
        "non-abstained answer requires at least one citation",
    )


def test_abstention_does_not_require_citation() -> None:
    request = make_request()

    answer = GroundedAnswer(
        abstained=True,
        abstention_reason="evidence is insufficient",
    )

    result = verify_grounding(
        request=request,
        answer=answer,
    )

    assert result.valid is True

def test_abstention_cannot_contain_answer_text() -> None:
    with pytest.raises(ValidationError):
        GroundedAnswer(
            answer="Unsupported answer.",
            abstained=True,
            abstention_reason="insufficient evidence",
        )


def test_abstention_cannot_contain_citations() -> None:
    with pytest.raises(ValidationError):
        GroundedAnswer(
            citations=(
                Citation(chunk_id=CHUNK_ID),
            ),
            abstained=True,
            abstention_reason="insufficient evidence",
        )