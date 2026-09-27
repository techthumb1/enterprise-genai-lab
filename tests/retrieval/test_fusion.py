from uuid import UUID

from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.models import RetrievalHit

DOCUMENT_ID = UUID(
    "018f0000-0000-7000-8000-000000000100"
)


def make_hit(
    suffix: int,
    *,
    score: float = 1.0,
) -> RetrievalHit:
    chunk_id = UUID(
        f"018f0000-0000-7000-8000-{suffix:012d}"
    )

    return RetrievalHit(
        chunk_id=chunk_id,
        document_id=DOCUMENT_ID,
        content=f"chunk {suffix}",
        score=score,
    )


def test_rrf_rewards_overlap() -> None:
    first = make_hit(1)
    second = make_hit(2)
    third = make_hit(3)

    fused = reciprocal_rank_fusion(
        rankings=(
            (first, second),
            (second, third),
        ),
        k=60,
        limit=3,
    )

    assert fused[0].chunk_id == second.chunk_id


def test_rrf_keeps_results_from_only_one_ranking() -> None:
    first = make_hit(1)
    second = make_hit(2)

    fused = reciprocal_rank_fusion(
        rankings=(
            (first,),
            (second,),
        ),
        k=60,
        limit=2,
    )

    assert {
        hit.chunk_id
        for hit in fused
    } == {
        first.chunk_id,
        second.chunk_id,
    }


def test_rrf_has_stable_tie_ordering() -> None:
    first = make_hit(1)
    second = make_hit(2)

    fused = reciprocal_rank_fusion(
        rankings=(
            (second,),
            (first,),
        ),
        k=60,
        limit=2,
    )

    assert [
        hit.chunk_id
        for hit in fused
    ] == [
        first.chunk_id,
        second.chunk_id,
    ]


def test_rrf_applies_top_k_limit() -> None:
    first = make_hit(1)
    second = make_hit(2)
    third = make_hit(3)

    fused = reciprocal_rank_fusion(
        rankings=((first, second, third),),
        k=60,
        limit=2,
    )

    assert len(fused) == 2
    assert fused[0].chunk_id == first.chunk_id
    assert fused[1].chunk_id == second.chunk_id