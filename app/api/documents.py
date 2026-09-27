from __future__ import annotations

from pathlib import PurePath
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request
from openai import OpenAIError
from pydantic import BaseModel

from app.api.dependencies import DocumentEmbedderDependency, DocumentIngestorDependency
from app.ingestion.media import UnsupportedMediaTypeError
from app.ingestion.parsers.base import DocumentParseError

router = APIRouter(prefix="/api/documents", tags=["documents"])
MAX_DOCUMENT_BYTES = 2 * 1024 * 1024


class DocumentUploadResponse(BaseModel):
    document_id: UUID
    processing_run_id: UUID
    chunk_count: int
    created: bool
    ready_for_retrieval: bool


@router.post("", response_model=DocumentUploadResponse)
async def upload_document(
    request: Request,
    ingestor: DocumentIngestorDependency,
    embedder: DocumentEmbedderDependency,
    filename: str = Query(min_length=1, max_length=255),
) -> DocumentUploadResponse:
    if (
        filename != PurePath(filename).name
        or "\\" in filename
        or filename.startswith(".")
        or not filename.lower().endswith((".txt", ".md", ".markdown"))
    ):
        raise HTTPException(status_code=415, detail="Choose a .txt or .md file")

    parts: list[bytes] = []
    total = 0
    async for part in request.stream():
        total += len(part)
        if total > MAX_DOCUMENT_BYTES:
            raise HTTPException(status_code=413, detail="Document exceeds the 2 MB limit")
        parts.append(part)

    try:
        result = await ingestor.ingest(
            filename=filename,
            content=b"".join(parts),
            declared_media_type=None,
        )
    except (DocumentParseError, ValueError, UnsupportedMediaTypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        while await embedder.embed_pending(processing_run_id=result.processing_run_id, limit=64):
            pass
    except OpenAIError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Document saved, but indexing is unavailable. "
                "Upload the same file again to resume."
            ),
        ) from exc

    return DocumentUploadResponse(
        document_id=result.document_id,
        processing_run_id=result.processing_run_id,
        chunk_count=result.chunk_count,
        created=result.created,
        ready_for_retrieval=True,
    )
