# API

## System endpoints

- `GET /health`: process health and version.
- `GET /ready`: database reachability.

## Governed answer

`POST /api/answer`

```json
{
  "query": "Why is the graph converted to a homogeneous graph?",
  "processing_run_id": "01a0e025-2603-7dbe-a393-0b3b653d7d02",
  "risk_tier": "standard"
}
```

The response includes workflow/provider/model identifiers, evidence count, final answer and citations, deterministic verification, risk disposition, and an optional review ID. Raw evidence and the candidate answer are intentionally omitted.

`high` risk creates a pending review after successful grounding verification. Invalid grounding abstains and never creates a review.

## Processing-run catalog

`GET /api/processing-runs?ready_only=true&limit=50`

Returns processing runs that the answer workbench can select. Each item contains document and run IDs, filename, parser/chunker versions, chunk and embedding counts, embedding provider/model, readiness, and creation time. It intentionally omits document content, checksums, source metadata, and credentials.

`ready_only` defaults to `true`. `limit` must be between 1 and 100.

## Human review

- `GET /api/reviews?status=pending&limit=50`: list review records by status.
- `GET /api/reviews/{review_id}`: retrieve a review record.
- `POST /api/reviews/{review_id}/decision`: approve or reject a pending review.

```json
{
  "status": "approved",
  "reviewer_id": "reviewer-123",
  "comment": "Evidence and citations support release."
}
```

Repeated or concurrent decisions return `409`. Missing reviews return `404`.

Review records include the unreleased candidate and captured evidence because reviewers need both to make a decision. Treat list and detail responses as sensitive document access, not as general answer APIs.

## Browser interface

FastAPI serves the compiled interface at `/` after API routes, so `/health`, `/ready`, and `/api/*` retain priority. The browser uses relative same-origin requests and contains no provider keys or database credentials. A missing frontend build does not prevent API startup; build `ui/dist` before serving the interface.

## Error semantics

- `422`: invalid typed request.
- `404`: unknown review or frontend asset.
- `409`: review already decided.
- `503`: provider not configured or temporarily unavailable.
- `502`: provider response violated the structured-output contract.

Authentication is deliberately outside the current lab scope and is mandatory before exposing document or review endpoints publicly.
