from uuid import UUID

from app.generation.context import (
    assemble_generation_request,
)
from app.retrieval.models import RetrievalHit

PROCESSING_RUN_ID = UUID(
    "018f0000-0000-7000-8000-000000000100"
)
DOCUMENT_ID = UUID(
    "018f0000-0000-7000-8000-000000000200"
)
CHUNK_ID = UUID(
    "018f0000-0000-7000-8000-000000000300"
)


def test_assemble_generation_request() -> None:
    hits = (
        RetrievalHit(
            chunk_id=CHUNK_ID,
            document_id=DOCUMENT_ID,
            content="Grounded evidence.",
            score=0.91,
        ),
    )

    request = assemble_generation_request(
        query="What does the evidence say?",
        processing_run_id=PROCESSING_RUN_ID,
        hits=hits,
    )

    assert request.query == "What does the evidence say?"
    assert request.processing_run_id == PROCESSING_RUN_ID
    assert len(request.evidence) == 1

    evidence = request.evidence[0]

    assert evidence.chunk_id == CHUNK_ID
    assert evidence.document_id == DOCUMENT_ID
    assert evidence.processing_run_id == PROCESSING_RUN_ID
    assert evidence.content == "Grounded evidence."