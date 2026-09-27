from __future__ import annotations

from uuid import UUID

import pytest

from app.ingestion.chunking.fixed_window import (
    FixedWindowChunker,
)
from app.ingestion.models import (
    IngestionDraft,
    PersistedDocument,
)
from app.ingestion.parsers.markdown import MarkdownParser
from app.ingestion.parsers.text import TextParser
from app.ingestion.service import IngestionService


class FakeRepository:
    def __init__(self) -> None:
        self.saved_drafts: list[IngestionDraft] = []
        self.documents: dict[str, PersistedDocument] = {}

    async def find_by_checksum(
        self,
        checksum_sha256: str,
    ) -> PersistedDocument | None:
        return self.documents.get(checksum_sha256)

    async def save(
        self,
        draft: IngestionDraft,
    ) -> PersistedDocument:
        self.saved_drafts.append(draft)

        document = PersistedDocument(
            document_id=UUID(
                "018f0000-0000-7000-8000-000000000001"
            ),
            processing_run_id=UUID(
                "018f0000-0000-7000-8000-000000000002"
            ),
            checksum_sha256=draft.checksum_sha256,
            chunk_count=len(draft.chunks),
            created=True,
        )

        self.documents[draft.checksum_sha256] = document

        return document


@pytest.mark.asyncio
async def test_ingestion_service_builds_versioned_processing_strategy() -> None:
    repository = FakeRepository()

    service = IngestionService(
        repository=repository,
        chunker=FixedWindowChunker(
            max_tokens=3,
            overlap_tokens=1,
        ),
        parsers=[
            TextParser(),
            MarkdownParser(),
        ],
    )

    first = await service.ingest(
        filename="sample.txt",
        declared_media_type="text/plain",
        content=b"alpha beta gamma delta epsilon",
        source_metadata={
            "source": "unit-test",
        },
    )

    assert first.created is True

    assert len(repository.saved_drafts) == 1

    draft = repository.saved_drafts[0]

    assert draft.strategy.parser_name == "plain-text"
    assert draft.strategy.parser_version == "1"
    assert draft.strategy.normalization_version == "utf8-lf-v1"

    assert draft.strategy.chunker_name == "fixed-token-window"
    assert draft.strategy.chunker_version == "1"

    assert draft.strategy.chunking_config == {
        "max_tokens": 3,
        "overlap_tokens": 1,
        "tokenizer": "whitespace-v1",
    }

    assert draft.source_metadata == {
        "source": "unit-test",
    }

    assert first.document_id == UUID(
        "018f0000-0000-7000-8000-000000000001"
    )
    assert first.processing_run_id == UUID(
        "018f0000-0000-7000-8000-000000000002"
    )

    assert len(repository.saved_drafts) == 1