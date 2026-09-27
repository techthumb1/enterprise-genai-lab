from __future__ import annotations

import argparse
import asyncio
from collections.abc import Sequence
from statistics import fmean
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.evaluation.retrieval import (
    ChunkSpan,
    LabeledQuery,
    SourceSpan,
    evaluate_ranking,
    relevant_chunk_ids,
)
from app.models.document import DocumentChunk
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.openai_embeddings import OpenAIEmbeddingProvider
from app.retrieval.service import RetrievalService
from app.retrieval.sqlalchemy_repository import (
    SQLAlchemyRetrievalRepository,
)

BASELINE_RUN_ID = UUID(
    "01a0df9d-c34c-7d81-bcb4-9d1541d31518"
)
STRUCTURED_RUN_ID = UUID(
    "01a0e025-2603-7dbe-a393-0b3b653d7d02"
)

RETRIEVAL_LIMIT = 10
RRF_K = 60
K_VALUES = (1, 3, 5)

STEP_1 = SourceSpan(start_char=532, end_char=1150)
STEP_2 = SourceSpan(start_char=1151, end_char=1540)
STEP_3 = SourceSpan(start_char=1541, end_char=2169)
STEP_4 = SourceSpan(start_char=2170, end_char=2551)
STEP_5 = SourceSpan(start_char=2552, end_char=3030)
STEP_6 = SourceSpan(start_char=3031, end_char=3316)
CONCLUSION = SourceSpan(start_char=3318, end_char=3798)

BENCHMARK = (
    LabeledQuery(
        name="drugbank-content",
        query="What information does DrugBank contain?",
        relevant_spans=(STEP_1,),
    ),
    LabeledQuery(
        name="entity-mapping",
        query=(
            "How are raw IDs, labels, and relationship types "
            "normalized before graph construction?"
        ),
        relevant_spans=(STEP_2,),
    ),
    LabeledQuery(
        name="heterogeneous-relations",
        query=(
            "How are drug-protein and drug-disease relationships "
            "represented in the heterogeneous graph?"
        ),
        relevant_spans=(STEP_3,),
    ),
    LabeledQuery(
        name="homogeneous-purpose",
        query=(
            "Why might the graph be converted to a homogeneous "
            "graph for GraphSAGE?"
        ),
        relevant_spans=(STEP_4,),
    ),
    LabeledQuery(
        name="homogeneous-features",
        query=(
            "What node features are added when the homogeneous "
            "graph has no x attribute?"
        ),
        relevant_spans=(STEP_4,),
    ),
    LabeledQuery(
        name="negative-sampling",
        query=(
            "How are negative drug-pair samples generated for "
            "link prediction?"
        ),
        relevant_spans=(STEP_5,),
    ),
    LabeledQuery(
        name="validation",
        query=(
            "What graph checks are performed before training?"
        ),
        relevant_spans=(STEP_6,),
    ),
    LabeledQuery(
        name="semantic-relationships",
        query=(
            "Why is preserving semantic relationships important "
            "in the heterogeneous graph?"
        ),
        relevant_spans=(STEP_3,),
    ),
    LabeledQuery(
        name="graph-purpose",
        query=(
            "What is the biomedical knowledge graph ultimately "
            "used as a foundation for?"
        ),
        relevant_spans=(CONCLUSION,),
    ),
    LabeledQuery(
        name="datasets-to-entities",
        query=(
            "How does the workflow move from selecting biomedical "
            "datasets to mapping entities and relations?"
        ),
        relevant_spans=(STEP_1, STEP_2),
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate baseline and structured retrieval "
            "against source-grounded labels."
        ),
    )
    parser.add_argument(
        "--baseline-run-id",
        type=UUID,
        default=BASELINE_RUN_ID,
    )
    parser.add_argument(
        "--structured-run-id",
        type=UUID,
        default=STRUCTURED_RUN_ID,
    )
    return parser.parse_args()


async def load_chunk_spans(
    session: AsyncSession,
    *,
    processing_run_id: UUID,
) -> tuple[ChunkSpan, ...]:
    statement = (
        select(
            DocumentChunk.id,
            DocumentChunk.chunk_metadata,
        )
        .where(
            DocumentChunk.processing_run_id
            == processing_run_id
        )
        .order_by(DocumentChunk.chunk_index)
    )

    result = await session.execute(statement)

    chunks: list[ChunkSpan] = []

    for row in result:
        raw_span = row.chunk_metadata.get(
            "source_span"
        )

        if raw_span is None:
            raise RuntimeError(
                "chunk is missing source_span metadata: "
                f"{row.id}"
            )

        chunks.append(
            ChunkSpan(
                chunk_id=row.id,
                source_span=SourceSpan(
                    start_char=raw_span["start_char"],
                    end_char=raw_span["end_char"],
                ),
            )
        )

    if not chunks:
        raise RuntimeError(
            "processing run contains no chunks: "
            f"{processing_run_id}"
        )

    return tuple(chunks)


def summarize(
    *,
    rankings: Sequence[Sequence[UUID]],
    relevant_sets: Sequence[set[UUID]],
) -> tuple[float, float, float, float]:
    recalls: dict[int, list[float]] = {
        k: []
        for k in K_VALUES
    }
    reciprocal_ranks: list[float] = []

    for retrieved, relevant in zip(
        rankings,
        relevant_sets,
        strict=True,
    ):
        for k in K_VALUES:
            metrics = evaluate_ranking(
                retrieved=retrieved,
                relevant=relevant,
                k=k,
            )
            recalls[k].append(
                metrics.recall_at_k
            )

        reciprocal_ranks.append(
            evaluate_ranking(
                retrieved=retrieved,
                relevant=relevant,
                k=RETRIEVAL_LIMIT,
            ).reciprocal_rank
        )

    return (
        fmean(recalls[1]),
        fmean(recalls[3]),
        fmean(recalls[5]),
        fmean(reciprocal_ranks),
    )


async def evaluate_run(
    *,
    label: str,
    processing_run_id: UUID,
    session: AsyncSession,
    service: RetrievalService,
) -> list[tuple[str, str, float, float, float, float]]:
    chunks = await load_chunk_spans(
        session,
        processing_run_id=processing_run_id,
    )

    rankings: dict[str, list[tuple[UUID, ...]]] = {
        "lexical": [],
        "vector": [],
        "hybrid": [],
    }
    relevant_sets: list[set[UUID]] = []

    hybrid_misses: list[str] = []

    for case in BENCHMARK:
        relevant = relevant_chunk_ids(
            chunks=chunks,
            relevant_spans=case.relevant_spans,
        )

        if not relevant:
            raise RuntimeError(
                "benchmark case has no relevant chunks "
                f"for {label}: {case.name}"
            )

        lexical = await service.lexical_search(
            processing_run_id=processing_run_id,
            query=case.query,
            limit=RETRIEVAL_LIMIT,
        )

        vector = await service.vector_search(
            processing_run_id=processing_run_id,
            query=case.query,
            limit=RETRIEVAL_LIMIT,
        )

        hybrid = reciprocal_rank_fusion(
            rankings=(lexical, vector),
            k=RRF_K,
            limit=RETRIEVAL_LIMIT,
        )

        lexical_ids = tuple(
            hit.chunk_id
            for hit in lexical
        )
        vector_ids = tuple(
            hit.chunk_id
            for hit in vector
        )
        hybrid_ids = tuple(
            hit.chunk_id
            for hit in hybrid
        )

        rankings["lexical"].append(lexical_ids)
        rankings["vector"].append(vector_ids)
        rankings["hybrid"].append(hybrid_ids)
        relevant_sets.append(relevant)

        if not relevant.intersection(
            hybrid_ids[:3]
        ):
            hybrid_misses.append(case.name)

    rows = []

    for mode in (
        "lexical",
        "vector",
        "hybrid",
    ):
        recall_1, recall_3, recall_5, mrr = summarize(
            rankings=rankings[mode],
            relevant_sets=relevant_sets,
        )

        rows.append(
            (
                label,
                mode,
                recall_1,
                recall_3,
                recall_5,
                mrr,
            )
        )

    if hybrid_misses:
        print(
            f"\n{label.upper()} HYBRID MISSES @3:"
        )
        for name in hybrid_misses:
            print(f"  - {name}")
    else:
        print(
            f"\n{label.upper()} HYBRID MISSES @3: none"
        )

    return rows


def print_results(
    rows: Sequence[
        tuple[
            str,
            str,
            float,
            float,
            float,
            float,
        ]
    ],
) -> None:
    print()
    print(
        f"{'RUN':<12}"
        f"{'MODE':<10}"
        f"{'R@1':>8}"
        f"{'R@3':>8}"
        f"{'R@5':>8}"
        f"{'MRR':>8}"
    )
    print("-" * 54)

    for (
        run,
        mode,
        recall_1,
        recall_3,
        recall_5,
        mrr,
    ) in rows:
        print(
            f"{run:<12}"
            f"{mode:<10}"
            f"{recall_1:>8.3f}"
            f"{recall_3:>8.3f}"
            f"{recall_5:>8.3f}"
            f"{mrr:>8.3f}"
        )


async def main(
    baseline_run_id: UUID,
    structured_run_id: UUID,
) -> None:
    settings = get_settings()

    if settings.openai_api_key is None:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured"
        )

    provider = OpenAIEmbeddingProvider(
        api_key=(
            settings.openai_api_key.get_secret_value()
        ),
        model="text-embedding-3-small",
    )

    async with get_session_factory()() as session:
        repository = SQLAlchemyRetrievalRepository(
            session
        )
        service = RetrievalService(
            repository=repository,
            embedding_provider=provider,
        )

        rows = []

        rows.extend(
            await evaluate_run(
                label="baseline",
                processing_run_id=baseline_run_id,
                session=session,
                service=service,
            )
        )

        rows.extend(
            await evaluate_run(
                label="structured",
                processing_run_id=structured_run_id,
                session=session,
                service=service,
            )
        )

        print_results(rows)


if __name__ == "__main__":
    args = parse_args()

    asyncio.run(
        main(
            args.baseline_run_id,
            args.structured_run_id,
        )
    )
