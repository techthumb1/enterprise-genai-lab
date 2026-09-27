from __future__ import annotations

from pathlib import Path

TEXT_PLAIN = "text/plain"
TEXT_MARKDOWN = "text/markdown"

_EXTENSION_MEDIA_TYPES = {
    ".txt": TEXT_PLAIN,
    ".md": TEXT_MARKDOWN,
    ".markdown": TEXT_MARKDOWN,
}

_MARKDOWN_MEDIA_TYPES = {
    "text/markdown",
    "text/x-markdown",
}


class UnsupportedMediaTypeError(ValueError):
    pass


def resolve_media_type(
    filename: str,
    declared_media_type: str | None,
) -> str:
    suffix = Path(filename).suffix.lower()

    declared = (
        declared_media_type.split(";", maxsplit=1)[0].strip().lower()
        if declared_media_type
        else None
    )

    expected = _EXTENSION_MEDIA_TYPES.get(suffix)

    if expected == TEXT_MARKDOWN:
        if declared in {
            None,
            "application/octet-stream",
            TEXT_PLAIN,
            *_MARKDOWN_MEDIA_TYPES,
        }:
            return TEXT_MARKDOWN

        raise UnsupportedMediaTypeError(
            f"Unexpected media type for Markdown file: {declared}"
        )

    if expected == TEXT_PLAIN:
        if declared in {
            None,
            "application/octet-stream",
            TEXT_PLAIN,
        }:
            return TEXT_PLAIN

        raise UnsupportedMediaTypeError(
            f"Unexpected media type for text file: {declared}"
        )

    if declared == TEXT_PLAIN:
        return TEXT_PLAIN

    if declared in _MARKDOWN_MEDIA_TYPES:
        return TEXT_MARKDOWN

    raise UnsupportedMediaTypeError(
        f"Unsupported document type: filename={filename!r}, "
        f"media_type={declared_media_type!r}"
    )