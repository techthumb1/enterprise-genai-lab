from __future__ import annotations

from typing import ClassVar, Protocol

from app.ingestion.models import (
    ChunkDraft,
    JsonObject,
    ParsedDocument,
)


class DocumentChunker(Protocol):
    name: ClassVar[str]
    version: ClassVar[str]

    @property
    def config(self) -> JsonObject:
        ...

    def chunk(
        self,
        document: ParsedDocument,
    ) -> tuple[ChunkDraft, ...]:
        ...