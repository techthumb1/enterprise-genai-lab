from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from app.retrieval.models import RetrievalHit


def reciprocal_rank_fusion(
    *,
    rankings: Sequence[Sequence[RetrievalHit]],
    k: int = 60,
    limit: int = 5,
) -> tuple[RetrievalHit, ...]:
    if k <= 0:
        raise ValueError("k must be greater than zero")

    if limit <= 0:
        raise ValueError("limit must be greater than zero")

    scores: dict[UUID, float] = {}
    best_ranks: dict[UUID, int] = {}
    hits: dict[UUID, RetrievalHit] = {}

    for ranking in rankings:
        seen: set[UUID] = set()

        for rank, hit in enumerate(ranking, start=1):
            if hit.chunk_id in seen:
                continue

            seen.add(hit.chunk_id)
            hits.setdefault(hit.chunk_id, hit)

            scores[hit.chunk_id] = (
                scores.get(hit.chunk_id, 0.0)
                + 1.0 / (k + rank)
            )

            best_ranks[hit.chunk_id] = min(
                best_ranks.get(hit.chunk_id, rank),
                rank,
            )

    ordered_ids = sorted(
        scores,
        key=lambda chunk_id: (
            -scores[chunk_id],
            best_ranks[chunk_id],
            str(chunk_id),
        ),
    )

    return tuple(
        hits[chunk_id].model_copy(
            update={"score": scores[chunk_id]}
        )
        for chunk_id in ordered_ids[:limit]
    )