from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar

from app.ingestion.models import (
    ChunkDraft,
    JsonObject,
    ParsedDocument,
)
from app.ingestion.provenance import LineIndex

"""
These are baseline lexical tokens, not provider- or model-specific tokens.
"""

_TOKEN_RE = re.compile(r"\S+")


@dataclass(frozen=True, slots=True)
class FixedWindowChunker:
    max_tokens: int = 320
    overlap_tokens: int = 40

    name: ClassVar[str] = "fixed-token-window"
    version: ClassVar[str] = "1"

    def __post_init__(self) -> None:
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")

        if self.overlap_tokens < 0:
            raise ValueError(
                "overlap_tokens cannot be negative"
            )

        if self.overlap_tokens >= self.max_tokens:
            raise ValueError(
                "overlap_tokens must be smaller than max_tokens"
            )

    @property
    def config(self) -> JsonObject:
        return {
            "max_tokens": self.max_tokens,
            "overlap_tokens": self.overlap_tokens,
            "tokenizer": "whitespace-v1",
        }

    def chunk(
        self,
        document: ParsedDocument,
    ) -> tuple[ChunkDraft, ...]:
        chunks: list[ChunkDraft] = []

        line_index = LineIndex.from_text(
            document.normalized_text
        )

        for section in document.sections:
            tokens = list(
                _TOKEN_RE.finditer(section.text)
            )

            if not tokens:
                continue

            token_start = 0

            while token_start < len(tokens):
                token_end = min(
                    token_start + self.max_tokens,
                    len(tokens),
                )

                first_token = tokens[token_start]
                last_token = tokens[token_end - 1]

                local_start = first_token.start()
                local_end = last_token.end()

                global_start = (
                    section.source_span.start_char
                    + local_start
                )

                global_end = (
                    section.source_span.start_char
                    + local_end
                )

                content = section.text[
                    local_start:local_end
                ]

                chunks.append(
                    ChunkDraft(
                        chunk_index=len(chunks),
                        section_ordinal=section.ordinal,
                        content=content,
                        section_title=section.title,
                        page_number=section.page_number,
                        token_count=(
                            token_end - token_start
                        ),
                        source_span=line_index.span(
                            global_start,
                            global_end,
                        ),
                        metadata={
                            "chunker": self.name,
                            "chunker_version": self.version,
                            "tokenizer": "whitespace-v1",
                        },
                    )
                )

                if token_end == len(tokens):
                    break

                token_start = (
                    token_end - self.overlap_tokens
                )

        return tuple(chunks)