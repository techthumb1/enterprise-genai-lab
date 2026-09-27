from __future__ import annotations

import argparse
import asyncio
from uuid import UUID

from app.core.config import get_settings
from app.db.session import SessionFactory
from app.retrieval.openai_embeddings import OpenAIEmbeddingProvider
from app.retrieval.service import RetrievalService
from app.retrieval.sqlalchemy_repository import (
    SQLAlchemyRetrievalRepository,
)

QUERIES = (
    "Which biomedical datasets are used to build the knowledge graph?",
    "Why would the graph be converted to a homogeneous graph?",
    "How are negative samples generated for training?",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare retrieval modes for one processing run.",
    )
    parser.add_argument(
        "--processing-run-id",
        required=True,
        type=UUID,
        help="Document processing run UUID to search.",
    )
    return parser.parse_args()


async def main(
    processing_run_id: UUID,
) -> None:
    settings = get_settings()

    if settings.openai_api_key is None:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    provider = OpenAIEmbeddingProvider(
        api_key=settings.openai_api_key.get_secret_value(),
        model="text-embedding-3-small",
    )

    async with SessionFactory() as session:
        repository = SQLAlchemyRetrievalRepository(session)

        service = RetrievalService(
            repository=repository,
            embedding_provider=provider,
        )

        print(f"PROCESSING RUN: {processing_run_id}")

        for query in QUERIES:
            lexical = await service.lexical_search(
                processing_run_id=processing_run_id,
                query=query,
                limit=5,
            )

            vector = await service.vector_search(
                processing_run_id=processing_run_id,
                query=query,
                limit=5,
            )

            print()
            print("=" * 80)
            print(f"QUERY: {query}")

            print("\nLEXICAL")
            if not lexical:
                print("  no results")

            for rank, hit in enumerate(lexical, start=1):
                preview = " ".join(hit.content.split())[:180]
                print(
                    f"  {rank}. score={hit.score:.6f} "
                    f"chunk={hit.chunk_id}"
                )
                print(f"     {preview}")

            print("\nVECTOR")
            if not vector:
                print("  no results")

            for rank, hit in enumerate(vector, start=1):
                preview = " ".join(hit.content.split())[:180]
                print(
                    f"  {rank}. score={hit.score:.6f} "
                    f"chunk={hit.chunk_id}"
                )
                print(f"     {preview}")


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args.processing_run_id))