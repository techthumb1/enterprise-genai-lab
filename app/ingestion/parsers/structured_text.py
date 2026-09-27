from __future__ import annotations

import re
from typing import ClassVar

from app.ingestion.models import ParsedDocument, ParsedSection
from app.ingestion.parsers.base import decode_text_document
from app.ingestion.provenance import LineIndex

_SECTION_HEADING = re.compile(
    (
        r"^[ \t]*"
        r"(?P<title>"
        r"(?:introduction|conclusion|"
        r"step\s+\d+(?:\s*[:.\-–—]\s*.*)?)"
        r")"
        r"[ \t]*$"
    ),
    flags=re.IGNORECASE | re.MULTILINE,
)


def _first_nonempty_line(text: str) -> str | None:
    for line in text.splitlines():
        title = line.strip()

        if title:
            return title

    return None


class StructuredTextParser:
    name: ClassVar[str] = "structured-text"
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

        matches = tuple(_SECTION_HEADING.finditer(text))

        if not matches:
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

        sections: list[ParsedSection] = []

        preamble_end = matches[0].start()
        preamble = text[:preamble_end]

        if preamble.strip():
            sections.append(
                ParsedSection(
                    ordinal=len(sections),
                    text=preamble,
                    title=_first_nonempty_line(preamble),
                    page_number=None,
                    source_span=line_index.span(
                        0,
                        preamble_end,
                    ),
                )
            )

        for index, match in enumerate(matches):
            start_char = match.start()

            end_char = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(text)
        )

            sections.append(
                ParsedSection(
                    ordinal=len(sections),
                    text=text[start_char:end_char],
                    title=match.group("title").strip(),
                    page_number=None,
                    source_span=line_index.span(
                        start_char,
                        end_char,
                    ),
                )
            )

        return ParsedDocument(
            filename=filename,
            media_type=media_type,
            normalized_text=text,
            parser_name=self.name,
            parser_version=self.version,
            normalization_version=self.normalization_version,
            sections=tuple(sections),
        )