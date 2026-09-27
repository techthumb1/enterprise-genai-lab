from app.ingestion.chunking.fixed_window import (
    FixedWindowChunker,
)
from app.ingestion.parsers.structured_text import StructuredTextParser
from app.ingestion.parsers.text import TextParser


def test_fixed_window_chunker_is_deterministic() -> None:
    document = TextParser().parse(
        filename="sample.txt",
        media_type="text/plain",
        content=(
            b"one two three four five six seven"
        ),
    )

    chunker = FixedWindowChunker(
        max_tokens=4,
        overlap_tokens=1,
    )

    first = chunker.chunk(document)
    second = chunker.chunk(document)

    assert first == second

    assert [
        chunk.content
        for chunk in first
    ] == [
        "one two three four",
        "four five six seven",
    ]


def test_chunk_source_spans_match_original_text() -> None:
    document = TextParser().parse(
        filename="sample.txt",
        media_type="text/plain",
        content=b"alpha beta gamma delta epsilon",
    )

    chunks = FixedWindowChunker(
        max_tokens=3,
        overlap_tokens=1,
    ).chunk(document)

    for chunk in chunks:
        extracted = document.normalized_text[
            chunk.source_span.start_char:
            chunk.source_span.end_char
        ]

        assert extracted == chunk.content

def test_fixed_window_chunker_respects_structured_sections() -> None:
    document = StructuredTextParser().parse(
        filename="structured.txt",
        media_type="text/plain",
        content=(
            b"Biomedical Knowledge Graph\n"
            b"Overview text.\n"
            b"\n"
            b"Step 1: Collect Data\n"
            b"alpha beta gamma\n"
            b"\n"
            b"Step 2: Normalize Data\n"
            b"delta epsilon zeta\n"
            b"\n"
            b"Conclusion\n"
            b"eta theta iota\n"
        ),
    )

    chunks = FixedWindowChunker(
        max_tokens=320,
        overlap_tokens=40,
    ).chunk(document)

    assert len(chunks) == len(document.sections)

    assert [
        chunk.section_title
        for chunk in chunks
    ] == [
        section.title
        for section in document.sections
    ]

    for chunk in chunks:
        section = document.sections[chunk.section_ordinal]

        assert (
            chunk.source_span.start_char
            >= section.source_span.start_char
        )
        assert (
            chunk.source_span.end_char
            <= section.source_span.end_char
        )

        extracted = document.normalized_text[
            chunk.source_span.start_char:
            chunk.source_span.end_char
        ]

        assert extracted == chunk.content


def test_fixed_window_chunker_splits_only_inside_large_section() -> None:
    document = StructuredTextParser().parse(
        filename="structured.txt",
        media_type="text/plain",
        content=(
            b"Step 1: Large Section\n"
            b"one two three four five six seven eight\n"
            b"\n"
            b"Conclusion\n"
            b"done"
        ),
    )

    chunks = FixedWindowChunker(
        max_tokens=4,
        overlap_tokens=1,
    ).chunk(document)

    step_chunks = [
        chunk
        for chunk in chunks
        if chunk.section_title == "Step 1: Large Section"
    ]

    conclusion_chunks = [
        chunk
        for chunk in chunks
        if chunk.section_title == "Conclusion"
    ]

    assert len(step_chunks) > 1
    assert len(conclusion_chunks) == 1

    assert all(
        chunk.section_ordinal == 0
        for chunk in step_chunks
    )

    assert conclusion_chunks[0].section_ordinal == 1