from uuid import UUID

from app.generation.models import (
    EvidenceChunk,
    GenerationRequest,
)
from app.generation.openai_provider import _format_input

PROCESSING_RUN_ID = UUID(
    "018f0000-0000-7000-8000-000000000100"
)
DOCUMENT_ID = UUID(
    "018f0000-0000-7000-8000-000000000200"
)
CHUNK_ID = UUID(
    "018f0000-0000-7000-8000-000000000300"
)


def test_format_input_contains_only_selected_evidence() -> None:
    request = GenerationRequest(
        query="What does the evidence say?",
        processing_run_id=PROCESSING_RUN_ID,
        evidence=(
            EvidenceChunk(
                chunk_id=CHUNK_ID,
                document_id=DOCUMENT_ID,
                processing_run_id=PROCESSING_RUN_ID,
                content="Selected evidence.",
            ),
        ),
    )

    formatted = _format_input(request)

    assert "What does the evidence say?" in formatted
    assert str(CHUNK_ID) in formatted
    assert str(DOCUMENT_ID) in formatted
    assert "Selected evidence." in formatted