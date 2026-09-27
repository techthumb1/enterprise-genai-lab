from uuid import UUID

from fastapi.testclient import TestClient

from app.api.dependencies import get_document_embedder, get_document_ingestor
from app.ingestion.models import IngestionResult
from app.main import app

RUN_ID = UUID("018f0000-0000-7000-8000-000000000100")
DOCUMENT_ID = UUID("018f0000-0000-7000-8000-000000000200")


class FakeIngestor:
    async def ingest(
        self, *, filename: str, content: bytes, declared_media_type: str | None
    ) -> IngestionResult:
        assert filename == "policy.md"
        assert content == b"# Policy\nApproval requires review."
        assert declared_media_type is None
        return IngestionResult(
            document_id=DOCUMENT_ID,
            processing_run_id=RUN_ID,
            checksum_sha256="a" * 64,
            chunk_count=1,
            created=True,
        )


class FakeEmbedder:
    def __init__(self) -> None:
        self.calls = 0

    async def embed_pending(self, *, processing_run_id: UUID, limit: int) -> int:
        assert processing_run_id == RUN_ID
        assert limit == 64
        self.calls += 1
        return 1 if self.calls == 1 else 0


def test_upload_indexes_document_and_returns_selected_run() -> None:
    embedder = FakeEmbedder()
    app.dependency_overrides[get_document_ingestor] = lambda: FakeIngestor()
    app.dependency_overrides[get_document_embedder] = lambda: embedder
    try:
        response = TestClient(app).post(
            "/api/documents?filename=policy.md",
            content=b"# Policy\nApproval requires review.",
            headers={"Content-Type": "application/octet-stream"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["processing_run_id"] == str(RUN_ID)
    assert response.json()["ready_for_retrieval"] is True
    assert embedder.calls == 2


def test_upload_rejects_large_or_unsupported_files_before_ingestion() -> None:
    app.dependency_overrides[get_document_ingestor] = lambda: FakeIngestor()
    app.dependency_overrides[get_document_embedder] = lambda: FakeEmbedder()
    try:
        client = TestClient(app)
        unsupported = client.post("/api/documents?filename=private.pdf", content=b"PDF")
        oversized = client.post(
            "/api/documents?filename=policy.md", content=b"a" * (2 * 1024 * 1024 + 1)
        )
    finally:
        app.dependency_overrides.clear()

    assert unsupported.status_code == 415
    assert oversized.status_code == 413
