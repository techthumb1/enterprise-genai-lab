from __future__ import annotations

import asyncio
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_session_factory
from app.ingestion.chunking.fixed_window import FixedWindowChunker
from app.ingestion.parsers.structured_text import StructuredTextParser
from app.ingestion.service import IngestionService
from app.ingestion.sqlalchemy_repository import SQLAlchemyIngestionRepository
from app.models.document import DocumentProcessingRun

SAMPLE_PATH = Path(
    "/Users/jasonrobinson/Documents/enterprise-genai-lab/"
    "samples/2. Building KG Drug Discovery.txt"
)


async def main() -> None:
    content = await asyncio.to_thread(SAMPLE_PATH.read_bytes)

    async with get_session_factory()() as session:
        repository = SQLAlchemyIngestionRepository(session)

        service = IngestionService(
            repository=repository,
            chunker=FixedWindowChunker(),
            parsers=[StructuredTextParser()],
        )

        result = await service.ingest(
            filename=SAMPLE_PATH.name,
            content=content,
            declared_media_type="text/plain",
            source_metadata={
                "source": "retained-sample",
                "purpose": "structured-retrieval-experiment",
            },
        )

        statement = (
            select(DocumentProcessingRun)
            .options(
                selectinload(DocumentProcessingRun.chunks),
                selectinload(DocumentProcessingRun.document),
            )
            .where(
                DocumentProcessingRun.id
                == result.processing_run_id
            )
        )

        run = (await session.execute(statement)).scalar_one()

        print("\nPROCESSING RESULT")
        print(result.model_dump())

        print("\nPROCESSING RUN")
        print(f"id: {run.id}")
        print(f"document_id: {run.document_id}")
        print(f"strategy_key: {run.strategy_key}")
        print(f"parser: {run.parser_name} / {run.parser_version}")
        print(
            "normalization_version: "
            f"{run.normalization_version}"
        )
        print(f"chunker: {run.chunker_name} / {run.chunker_version}")
        print(f"chunking_config: {run.chunking_config}")

        print("\nCHUNKS")

        for chunk in sorted(
            run.chunks,
            key=lambda item: item.chunk_index,
        ):
            metadata = chunk.chunk_metadata

            print(
                {
                    "chunk_index": chunk.chunk_index,
                    "section_title": chunk.section_title,
                    "token_count": chunk.token_count,
                    "section_ordinal": metadata.get(
                        "section_ordinal"
                    ),
                    "source_span": metadata.get("source_span"),
                }
            )


if __name__ == "__main__":
    asyncio.run(main())
