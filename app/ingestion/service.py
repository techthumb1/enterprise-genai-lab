from __future__ import annotations

from collections.abc import Iterable

from app.ingestion.chunking.base import (
    DocumentChunker,
)
from app.ingestion.hashing import sha256_bytes
from app.ingestion.media import resolve_media_type
from app.ingestion.models import (
    IngestionDraft,
    IngestionResult,
    JsonObject,
    ProcessingStrategy,
)
from app.ingestion.parsers.base import DocumentParser
from app.ingestion.repository import (
    IngestionRepository,
)


class ParserRegistrationError(ValueError):
    pass


class ParserNotFoundError(ValueError):
    pass


class IngestionService:
    def __init__(
        self,
        *,
        repository: IngestionRepository,
        chunker: DocumentChunker,
        parsers: Iterable[DocumentParser],
    ) -> None:
        self._repository = repository
        self._chunker = chunker

        parser_map: dict[str, DocumentParser] = {}

        for parser in parsers:
            for media_type in parser.supported_media_types:
                if media_type in parser_map:
                    raise ParserRegistrationError(
                        "Multiple parsers registered for "
                        f"{media_type!r}"
                    )

                parser_map[media_type] = parser

        self._parsers = parser_map

    async def ingest(
        self,
        *,
        filename: str,
        content: bytes,
        declared_media_type: str | None = None,
        source_metadata: JsonObject | None = None,
    ) -> IngestionResult:
        media_type = resolve_media_type(
            filename,
            declared_media_type,
        )

        checksum = sha256_bytes(content)

        parser = self._parsers.get(media_type)

        if parser is None:
            raise ParserNotFoundError(
                f"No parser registered for {media_type!r}"
            )

        parsed = parser.parse(
            filename=filename,
            media_type=media_type,
            content=content,
        )

        chunks = self._chunker.chunk(parsed)

        if not chunks:
            raise ValueError(
                "document produced no ingestible chunks"
            )

        strategy = ProcessingStrategy(
            parser_name=parsed.parser_name,
            parser_version=parsed.parser_version,
            normalization_version=(
                parsed.normalization_version
            ),
            chunker_name=self._chunker.name,
            chunker_version=self._chunker.version,
            chunking_config=self._chunker.config,
        )

        draft = IngestionDraft(
            filename=filename,
            media_type=media_type,
            checksum_sha256=checksum,
            strategy=strategy,
            source_metadata=source_metadata or {},
            processing_metadata={},
            sections=parsed.sections,
            chunks=chunks,
        )

        stored = await self._repository.save(draft)

        return IngestionResult(
            document_id=stored.document_id,
            processing_run_id=(
                stored.processing_run_id
            ),
            checksum_sha256=(
                stored.checksum_sha256
            ),
            chunk_count=stored.chunk_count,
            created=stored.created,
        )