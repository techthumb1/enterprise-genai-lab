from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProcessingRunSummary(BaseModel):
    """Non-sensitive processing-run metadata exposed to the UI."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    document_id: UUID
    filename: str = Field(min_length=1)
    parser_name: str = Field(min_length=1)
    parser_version: str = Field(min_length=1)
    chunker_name: str = Field(min_length=1)
    chunker_version: str = Field(min_length=1)
    chunk_count: int = Field(ge=0)
    embedded_chunk_count: int = Field(ge=0)
    embedding_provider: str = Field(min_length=1)
    embedding_model: str = Field(min_length=1)
    ready_for_retrieval: bool
    created_at: datetime


class ProcessingRunCatalog(Protocol):
    async def list_runs(
        self,
        *,
        ready_only: bool,
        limit: int,
    ) -> tuple[ProcessingRunSummary, ...]: ...
