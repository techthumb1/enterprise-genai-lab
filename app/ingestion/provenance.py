from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass

from app.ingestion.models import SourceSpan


@dataclass(frozen=True, slots=True)
class LineIndex:
    text_length: int
    line_starts: tuple[int, ...]

    @classmethod
    def from_text(cls, text: str) -> LineIndex:
        starts = [0]

        for index, character in enumerate(text):
            if character == "\n" and index + 1 < len(text):
                starts.append(index + 1)

        return cls(
            text_length=len(text),
            line_starts=tuple(starts),
        )

    def span(
        self,
        start_char: int,
        end_char: int,
    ) -> SourceSpan:
        if start_char < 0:
            raise ValueError("start_char cannot be negative")

        if end_char > self.text_length:
            raise ValueError("end_char exceeds text length")

        if end_char <= start_char:
            raise ValueError("end_char must be greater than start_char")

        start_line = bisect_right(
            self.line_starts,
            start_char,
        )

        end_line = bisect_right(
            self.line_starts,
            end_char - 1,
        )

        return SourceSpan(
            start_char=start_char,
            end_char=end_char,
            start_line=start_line,
            end_line=end_line,
        )