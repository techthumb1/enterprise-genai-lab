from __future__ import annotations

import argparse
import asyncio
from uuid import UUID

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.generation.context import (
    assemble_generation_request,
)
from app.generation.openai_provider import (
    OpenAIGenerationProvider,
)
from app.generation.service import GenerationService
from app.retrieval.openai_embeddings import (
    OpenAIEmbeddingProvider,
)
from app.retrieval.service import RetrievalService
from app.retrieval.sqlalchemy_repository import (
    SQLAlchemyRetrievalRepository,
)

DEFAULT_PROCESSING_RUN_ID = UUID(
    "01a0e025-2603-7dbe-a393-0b3b653d7d02"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a governed answer from retrieved document evidence."
        ),
    )

    parser.add_argument(
        "query",
        help="Question to answer from the selected document evidence.",
    )

    parser.add_argument(
        "--processing-run-id",
        type=UUID,
        default=DEFAULT_PROCESSING_RUN_ID,
    )

    parser.add_argument(
        "--model",
        default="gpt-5.6-luna",
        help="OpenAI generation model.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of retrieved evidence chunks.",
    )

    return parser.parse_args()


async def main(
    *,
    query: str,
    processing_run_id: UUID,
    model: str,
    limit: int,
) -> None:
    settings = get_settings()

    if settings.openai_api_key is None:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured"
        )

    api_key = (
        settings.openai_api_key.get_secret_value()
    )

    embedding_provider = OpenAIEmbeddingProvider(
        api_key=api_key,
        model="text-embedding-3-small",
    )

    generation_provider = OpenAIGenerationProvider(
        api_key=api_key,
        model=model,
    )

    async with get_session_factory()() as session:
        repository = SQLAlchemyRetrievalRepository(
            session
        )

        retrieval = RetrievalService(
            repository=repository,
            embedding_provider=embedding_provider,
        )

        hits = await retrieval.vector_search(
            processing_run_id=processing_run_id,
            query=query,
            limit=limit,
        )

        request = assemble_generation_request(
            query=query,
            processing_run_id=processing_run_id,
            hits=hits,
        )

        generation = GenerationService(
            provider=generation_provider,
        )

        result = await generation.generate(
            request
        )

    print()
    print("PROVIDER")
    print(f"  {result.provider}")

    print("\nMODEL")
    print(f"  {result.model}")

    print("\nRETRIEVED EVIDENCE")
    for rank, hit in enumerate(hits, start=1):
        print(
            f"  {rank}. "
            f"score={hit.score:.6f} "
            f"chunk={hit.chunk_id}"
        )

    print("\nCANDIDATE")
    print(
        result.candidate_answer.model_dump_json(
            indent=2
        )
        if result.candidate_answer is not None
        else "  none"
    )

    print("\nVERIFICATION")
    print(
        result.verification.model_dump_json(
            indent=2
        )
    )

    print("\nFINAL")
    print(
        result.final_answer.model_dump_json(
            indent=2
        )
    )


if __name__ == "__main__":
    args = parse_args()

    asyncio.run(
        main(
            query=args.query,
            processing_run_id=args.processing_run_id,
            model=args.model,
            limit=args.limit,
        )
    )
