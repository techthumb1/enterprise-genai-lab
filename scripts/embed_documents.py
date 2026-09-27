from __future__ import annotations

import argparse
import asyncio
from uuid import UUID

from app.core.config import get_settings
from app.db.session import SessionFactory
from app.retrieval.embedding_service import EmbeddingService
from app.retrieval.openai_embeddings import OpenAIEmbeddingProvider
from app.retrieval.sqlalchemy_repository import (
    SQLAlchemyRetrievalRepository,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Embed chunks for one processing run.",
    )
    parser.add_argument(
        "--processing-run-id",
        required=True,
        type=UUID,
        help="Document processing run UUID to embed.",
    )
    return parser.parse_args()


async def main(
    processing_run_id: UUID,
) -> None:
    settings = get_settings()

    api_key = (
        settings.openai_api_key.get_secret_value().strip()
        if settings.openai_api_key is not None
        else ""
    )

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured or is empty"
        )

    provider = OpenAIEmbeddingProvider(
        api_key=api_key,
        model="text-embedding-3-small",
    )

    total = 0

    async with SessionFactory() as session:
        repository = SQLAlchemyRetrievalRepository(session)

        service = EmbeddingService(
            repository=repository,
            provider=provider,
        )

        while True:
            inserted = await service.embed_pending(
                processing_run_id=processing_run_id,
                limit=64,
            )

            if inserted == 0:
                break

            total += inserted

    print(
        {
            "processing_run_id": str(processing_run_id),
            "provider": provider.provider,
            "model": provider.model,
            "embedded_chunks": total,
        }
    )


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args.processing_run_id))