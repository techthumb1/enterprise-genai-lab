from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from app.api.dependencies import get_processing_run_catalog
from app.catalog.models import ProcessingRunSummary
from app.main import app

RUN_ID = UUID("018f0000-0000-7000-8000-000000000100")
DOCUMENT_ID = UUID("018f0000-0000-7000-8000-000000000200")


class FakeProcessingRunCatalog:
    async def list_runs(
        self,
        *,
        ready_only: bool,
        limit: int,
    ) -> tuple[ProcessingRunSummary, ...]:
        assert ready_only is True
        assert limit == 50
        return (
            ProcessingRunSummary(
                id=RUN_ID,
                document_id=DOCUMENT_ID,
                filename="governance-policy.pdf",
                parser_name="pymupdf",
                parser_version="1.0",
                chunker_name="recursive-character",
                chunker_version="1.0",
                chunk_count=12,
                embedded_chunk_count=12,
                embedding_provider="openai",
                embedding_model="text-embedding-3-small",
                ready_for_retrieval=True,
                created_at=datetime(2026, 9, 26, 18, 30, tzinfo=UTC),
            ),
        )


def test_processing_runs_endpoint_returns_safe_catalog_metadata() -> None:
    app.dependency_overrides[get_processing_run_catalog] = (
        lambda: FakeProcessingRunCatalog()
    )
    try:
        response = TestClient(app).get("/api/processing-runs")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["id"] == str(RUN_ID)
    assert payload[0]["filename"] == "governance-policy.pdf"
    assert payload[0]["ready_for_retrieval"] is True
    assert "content" not in payload[0]
    assert "checksum" not in payload[0]
