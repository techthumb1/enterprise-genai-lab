from __future__ import annotations

import re
from typing import ClassVar

from app.ingestion.models import (
    JsonObject,
    ParsedDocument,
    ParsedSection,
)
from app.ingestion.parsers.base import decode_text_document
from app.ingestion.provenance import LineIndex

_HEADING_RE = re.compile(
    r"^[ \t]{0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*$"
)

_FENCE_RE = re.compile(
    r"^[ \t]{0,3}(`{3,}|~{3,})"
)


class MarkdownParser:
    name: ClassVar[str] = "markdown-atx"
    version: ClassVar[str] = "1"
    normalization_version: ClassVar[str] = "utf8-lf-v1"

    supported_media_types: ClassVar[frozenset[str]] = frozenset(
        {"text/markdown"}
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

        headings = self._find_headings(text)

        sections: tuple[ParsedSection, ...]

        if not headings:
            sections = (
                ParsedSection(
                    ordinal=0,
                    text=text,
                    title=None,
                    source_span=line_index.span(
                        0,
                        len(text),
                    ),
                ),
            )
        else:
            sections = self._build_sections(
                text=text,
                line_index=line_index,
                headings=headings,
            )
        
        return ParsedDocument(
            filename=filename,
            media_type=media_type,
            normalized_text=text,
            parser_name=self.name,
            parser_version=self.version,
            normalization_version=self.normalization_version,
            sections=sections,
        )

    def _find_headings(
        self,
        text: str,
    ) -> list[tuple[int, str | None, int]]:
        headings: list[tuple[int, str | None, int]] = []

        offset = 0

        fence_character: str | None = None
        fence_length = 0

        for raw_line in text.splitlines(keepends=True):
            line = raw_line.rstrip("\n")

            fence_match = _FENCE_RE.match(line)

            if fence_character is not None:
                if fence_match is not None:
                    marker = fence_match.group(1)

                    if (
                        marker[0] == fence_character
                        and len(marker) >= fence_length
                    ):
                        fence_character = None
                        fence_length = 0

                offset += len(raw_line)
                continue

            if fence_match is not None:
                marker = fence_match.group(1)

                fence_character = marker[0]
                fence_length = len(marker)

                offset += len(raw_line)
                continue

            heading_match = _HEADING_RE.match(line)

            if heading_match is not None:
                marker = heading_match.group(1)
                raw_title = heading_match.group(2) or ""

                title = re.sub(
                    r"[ \t]+#+[ \t]*$",
                    "",
                    raw_title,
                ).strip()

                headings.append(
                    (
                        offset,
                        title or None,
                        len(marker),
                    )
                )

            offset += len(raw_line)

        return headings

    def _build_sections(
        self,
        *,
        text: str,
        line_index: LineIndex,
        headings: list[tuple[int, str | None, int]],
    ) -> tuple[ParsedSection, ...]:
        sections: list[ParsedSection] = []

        first_heading_start = headings[0][0]

        if first_heading_start > 0:
            preamble = text[:first_heading_start]

            if preamble.strip():
                sections.append(
                    ParsedSection(
                        ordinal=len(sections),
                        text=preamble,
                        title=None,
                        source_span=line_index.span(
                            0,
                            first_heading_start,
                        ),
                    )
                )

        for index, heading in enumerate(headings):
            start_char, title, heading_level = heading

            end_char = (
                headings[index + 1][0]
                if index + 1 < len(headings)
                else len(text)
            )

            section_text = text[start_char:end_char]

            metadata: JsonObject = {
                "heading_level": heading_level,
            }

            sections.append(
                ParsedSection(
                    ordinal=len(sections),
                    text=section_text,
                    title=title,
                    source_span=line_index.span(
                        start_char,
                        end_char,
                    ),
                    metadata=metadata,
                )
            )

        return tuple(sections)