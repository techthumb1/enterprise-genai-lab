from __future__ import annotations

import hashlib
import json
from typing import Self
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

type JsonValue = (
    str
    | int
    | float
    | bool
    | None
    | list[JsonValue]
    | dict[str, JsonValue]
)

type JsonObject = dict[str, JsonValue]


class ContractModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class SourceSpan(ContractModel):
    start_char: int = Field(ge=0)
    end_char: int = Field(gt=0)
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_range(self) -> Self:
        if self.end_char <= self.start_char:
            raise ValueError(
                "end_char must be greater than start_char"
            )

        if self.end_line < self.start_line:
            raise ValueError(
                "end_line must be >= start_line"
            )

        return self


class ParsedSection(ContractModel):
    ordinal: int = Field(ge=0)
    text: str = Field(min_length=1)
    title: str | None = None
    page_number: int | None = Field(
        default=None,
        ge=1,
    )
    source_span: SourceSpan
    metadata: JsonObject = Field(
        default_factory=dict
    )


class ParsedDocument(ContractModel):
    filename: str = Field(min_length=1)
    media_type: str = Field(min_length=1)

    normalized_text: str = Field(min_length=1)

    parser_name: str = Field(min_length=1)
    parser_version: str = Field(min_length=1)
    normalization_version: str = Field(
        min_length=1
    )

    sections: tuple[ParsedSection, ...]


class ChunkDraft(ContractModel):
    chunk_index: int = Field(ge=0)
    section_ordinal: int = Field(ge=0)

    content: str = Field(min_length=1)

    section_title: str | None = None
    page_number: int | None = Field(
        default=None,
        ge=1,
    )

    token_count: int = Field(gt=0)
    source_span: SourceSpan

    metadata: JsonObject = Field(
        default_factory=dict
    )


class ProcessingStrategy(ContractModel):
    parser_name: str = Field(min_length=1)
    parser_version: str = Field(min_length=1)
    normalization_version: str = Field(
        min_length=1
    )

    chunker_name: str = Field(min_length=1)
    chunker_version: str = Field(min_length=1)

    chunking_config: JsonObject = Field(
        default_factory=dict
    )

    @property
    def strategy_key(self) -> str:
        payload = json.dumps(
            self.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        digest = hashlib.sha256(
            payload.encode("utf-8")
        ).hexdigest()

        return f"v1:{digest}"


class IngestionDraft(ContractModel):
    filename: str = Field(min_length=1)
    media_type: str = Field(min_length=1)

    checksum_sha256: str = Field(
        pattern=r"^[0-9a-f]{64}$",
    )

    strategy: ProcessingStrategy

    source_metadata: JsonObject = Field(
        default_factory=dict
    )

    processing_metadata: JsonObject = Field(
        default_factory=dict
    )

    sections: tuple[ParsedSection, ...]
    chunks: tuple[ChunkDraft, ...]


class PersistedDocument(ContractModel):
    document_id: UUID
    processing_run_id: UUID

    checksum_sha256: str = Field(
        pattern=r"^[0-9a-f]{64}$",
    )

    chunk_count: int = Field(ge=0)

    # True means this processing strategy was newly persisted.
    created: bool


class IngestionResult(ContractModel):
    document_id: UUID
    processing_run_id: UUID

    checksum_sha256: str = Field(
        pattern=r"^[0-9a-f]{64}$",
    )

    chunk_count: int = Field(ge=0)

    # True means this processing strategy was newly persisted.
    created: bool