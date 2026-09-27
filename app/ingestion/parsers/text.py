from __future__ import annotations

from typing import ClassVar

from app.ingestion.models import ParsedDocument, ParsedSection
from app.ingestion.parsers.base import decode_text_document
from app.ingestion.provenance import LineIndex


class TextParser:
    name: ClassVar[str] = "plain-text"
    version: ClassVar[str] = "1"
    normalization_version: ClassVar[str] = "utf8-lf-v1"

    supported_media_types: ClassVar[frozenset[str]] = frozenset(
        {"text/plain"}
    )

    def parse(
        self,
        *,
        filename: str,
        media_type: str,
        content: bytes,
    ) -> ParsedDocument:
        text = decode_text_document(content)
        line_index = LineIndex.from_text(text)

        section = ParsedSection(
            ordinal=0,
            text=text,
            title=None,
            page_number=None,
            source_span=line_index.span(
                0,
                len(text),
            ),
        )

        return ParsedDocument(
            filename=filename,
            media_type=media_type,
            normalized_text=text,
            parser_name=self.name,
            parser_version=self.version,
            normalization_version=self.normalization_version,
            sections=(section,),
        )