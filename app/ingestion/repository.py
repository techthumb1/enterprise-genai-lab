from __future__ import annotations

from typing import Protocol

from app.ingestion.models import (
    IngestionDraft,
    PersistedDocument,
)


class IngestionRepository(Protocol):
    async def save(
        self,
        draft: IngestionDraft,
    ) -> PersistedDocument:
        ...