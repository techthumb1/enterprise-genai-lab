from __future__ import annotations

from uuid import UUID

from app.generation.models import (
    EvidenceChunk,
    GenerationRequest,
)
from app.retrieval.models import RetrievalHit


def assemble_generation_request(
    *,
    query: str,
    processing_run_id: UUID,
    hits: tuple[RetrievalHit, ...],
) -> GenerationRequest:
    evidence = tuple(
        EvidenceChunk(
            chunk_id=hit.chunk_id,
            document_id=hit.document_id,
            processing_run_id=processing_run_id,
            content=hit.content,
        )
        for hit in hits
    )

    return GenerationRequest(
        query=query,
        processing_run_id=processing_run_id,
        evidence=evidence,
    )