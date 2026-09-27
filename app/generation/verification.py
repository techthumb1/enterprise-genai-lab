from __future__ import annotations

from app.generation.models import (
    GenerationRequest,
    GroundedAnswer,
    GroundingVerification,
)


def verify_grounding(
    *,
    request: GenerationRequest,
    answer: GroundedAnswer,
) -> GroundingVerification:
    errors: list[str] = []

    evidence_ids = {
        chunk.chunk_id
        for chunk in request.evidence
    }

    citation_ids = [
        citation.chunk_id
        for citation in answer.citations
    ]

    if len(set(citation_ids)) != len(citation_ids):
        errors.append("answer contains duplicate citations")

    unknown_ids = sorted(
        set(citation_ids) - evidence_ids,
        key=str,
    )

    for chunk_id in unknown_ids:
        errors.append(
            f"citation references unavailable chunk: {chunk_id}"
        )

    if not answer.abstained and not citation_ids:
        errors.append(
            "non-abstained answer requires at least one citation"
        )

    return GroundingVerification(
        valid=not errors,
        errors=tuple(errors),
    )