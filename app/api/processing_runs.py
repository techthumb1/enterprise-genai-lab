from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.dependencies import ProcessingRunCatalogDependency
from app.catalog.models import ProcessingRunSummary

router = APIRouter(prefix="/api/processing-runs", tags=["processing runs"])


@router.get("", response_model=list[ProcessingRunSummary])
async def list_processing_runs(
    catalog: ProcessingRunCatalogDependency,
    ready_only: Annotated[
        bool,
        Query(description="Return only runs fully embedded for retrieval."),
    ] = True,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> tuple[ProcessingRunSummary, ...]:
    return await catalog.list_runs(ready_only=ready_only, limit=limit)
