from __future__ import annotations

import asyncio
from pathlib import Path

from app.db.session import get_session_factory
from app.ingestion.chunking.fixed_window import FixedWindowChunker
from app.ingestion.parsers.text import TextParser
from app.ingestion.service import IngestionService
from app.ingestion.sqlalchemy_repository import SQLAlchemyIngestionRepository

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
            parsers=[TextParser()],
        )

        result = await service.ingest(
            filename=SAMPLE_PATH.name,
            content=content,
            declared_media_type="text/plain",
            source_metadata={
                "source": "retained-sample",
                "purpose": "document-intelligence-validation",
            },
        )

        print(result.model_dump())


if __name__ == "__main__":
    asyncio.run(main())
