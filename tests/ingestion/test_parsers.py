from app.ingestion.parsers.markdown import MarkdownParser
from app.ingestion.parsers.structured_text import StructuredTextParser
from app.ingestion.parsers.text import TextParser


def test_text_parser_normalizes_newlines() -> None:
    parser = TextParser()

    document = parser.parse(
        filename="sample.txt",
        media_type="text/plain",
        content=b"\xef\xbb\xbfline one\r\nline two\rline three",
    )

    assert document.normalized_text == (
        "line one\nline two\nline three"
    )

    assert len(document.sections) == 1

    section = document.sections[0]

    assert (
        document.normalized_text[
            section.source_span.start_char:
            section.source_span.end_char
        ]
        == section.text
    )


def test_markdown_parser_preserves_sections() -> None:
    parser = MarkdownParser()

    document = parser.parse(
        filename="sample.md",
        media_type="text/markdown",
        content=(
            b"Introduction\n\n"
            b"# First\n"
            b"Alpha\n\n"
            b"```md\n"
            b"# Not a heading\n"
            b"```\n\n"
            b"## Second\n"
            b"Beta\n"
        ),
    )

    assert [
        section.title
        for section in document.sections
    ] == [
        None,
        "First",
        "Second",
    ]

    for section in document.sections:
        extracted = document.normalized_text[
            section.source_span.start_char:
            section.source_span.end_char
        ]

        assert extracted == section.text


def test_markdown_heading_inside_fence_is_not_section() -> None:
    parser = MarkdownParser()

    document = parser.parse(
        filename="sample.md",
        media_type="text/markdown",
        content=(
            b"# Real heading\n"
            b"\n"
            b"```python\n"
            b"# fake heading\n"
            b"print('hello')\n"
            b"```\n"
        ),
    )

    assert len(document.sections) == 1
    assert document.sections[0].title == "Real heading"


def test_structured_text_parser_preserves_logical_sections() -> None:
    parser = StructuredTextParser()

    document = parser.parse(
        filename="structured.txt",
        media_type="text/plain",
        content=(
            b"Building a Biomedical Knowledge Graph\n"
            b"From Raw Data to Relational Intelligence\n"
            b"\n"
            b"Overview of the workflow.\n"
            b"\n"
            b"Step 1: Collect Source Data\n"
            b"Load biomedical datasets.\n"
            b"\n"
            b"Step 2 - Normalize Entities\n"
            b"Resolve identifiers and normalize records.\n"
            b"\n"
            b"Conclusion\n"
            b"The resulting graph supports discovery.\n"
        ),
    )

    assert document.parser_name == "structured-text"
    assert document.parser_version == "1"

    assert [
        section.title
        for section in document.sections
    ] == [
        "Building a Biomedical Knowledge Graph",
        "Step 1: Collect Source Data",
        "Step 2 - Normalize Entities",
        "Conclusion",
    ]

    assert [
        section.ordinal
        for section in document.sections
    ] == [
        0,
        1,
        2,
        3,
    ]

    for section in document.sections:
        extracted = document.normalized_text[
            section.source_span.start_char:
            section.source_span.end_char
        ]

        assert extracted == section.text


def test_structured_text_parser_falls_back_without_headings() -> None:
    parser = StructuredTextParser()

    document = parser.parse(
        filename="unstructured.txt",
        media_type="text/plain",
        content=(
            b"First paragraph without a structural heading.\n"
            b"\n"
            b"Second paragraph without one either."
        ),
    )

    assert len(document.sections) == 1

    section = document.sections[0]

    assert section.title is None
    assert section.ordinal == 0
    assert section.text == document.normalized_text

    extracted = document.normalized_text[
        section.source_span.start_char:
        section.source_span.end_char
    ]

    assert extracted == section.text