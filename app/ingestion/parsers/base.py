from __future__ import annotations

from typing import ClassVar, Protocol

from app.ingestion.models import ParsedDocument


class DocumentParseError(ValueError):
    pass


def decode_text_document(content: bytes) -> str:
    if not content:
        raise DocumentParseError("document is empty")

    if b"\x00" in content:
        raise DocumentParseError(
            "document contains NUL bytes and does not appear to be text"
        )

    try:
        text = content.decode(
            "utf-8-sig",
            errors="strict",
        )
    except UnicodeDecodeError as exc:
        raise DocumentParseError(
            "document must contain valid UTF-8 text"
        ) from exc

    normalized = (
        text.replace("\r\n", "\n")
        .replace("\r", "\n")
    )

    if not normalized.strip():
        raise DocumentParseError(
            "document contains no textual content"
        )

    return normalized


class DocumentParser(Protocol):
    name: ClassVar[str]
    version: ClassVar[str]
    normalization_version: ClassVar[str]
    supported_media_types: ClassVar[frozenset[str]]

    def parse(
        self,
        *,
        filename: str,
        media_type: str,
        content: bytes,
    ) -> ParsedDocument:
        ...