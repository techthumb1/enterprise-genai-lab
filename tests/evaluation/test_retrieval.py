from uuid import UUID

from app.evaluation.retrieval import (
    ChunkSpan,
    SourceSpan,
    evaluate_ranking,
    relevant_chunk_ids,
)


def test_evaluate_ranking() -> None:
    first = UUID(
        "018f0000-0000-7000-8000-000000000001"
    )
    second = UUID(
        "018f0000-0000-7000-8000-000000000002"
    )
    third = UUID(
        "018f0000-0000-7000-8000-000000000003"
    )

    metrics = evaluate_ranking(
        retrieved=[
            first,
            second,
            third,
        ],
        relevant={
            second,
            third,
        },
        k=2,
    )

    assert metrics.recall_at_k == 0.5
    assert metrics.reciprocal_rank == 0.5

def test_relevant_chunks_are_derived_from_source_spans() -> None:
    first = UUID(
        "018f0000-0000-7000-8000-000000000001"
    )
    second = UUID(
        "018f0000-0000-7000-8000-000000000002"
    )
    third = UUID(
        "018f0000-0000-7000-8000-000000000003"
    )

    chunks = (
        ChunkSpan(
            chunk_id=first,
            source_span=SourceSpan(
                start_char=0,
                end_char=150,
            ),
        ),
        ChunkSpan(
            chunk_id=second,
            source_span=SourceSpan(
                start_char=100,
                end_char=250,
            ),
        ),
        ChunkSpan(
            chunk_id=third,
            source_span=SourceSpan(
                start_char=300,
                end_char=400,
            ),
        ),
    )

    relevant = relevant_chunk_ids(
        chunks=chunks,
        relevant_spans=(
            SourceSpan(
                start_char=120,
                end_char=180,
            ),
        ),
    )

    assert relevant == {
        first,
        second,
    }