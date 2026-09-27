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

## Human review

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

## Error semantics

- `422`: invalid typed request.
- `404`: unknown review.
- `409`: review already decided.
- `503`: provider not configured or temporarily unavailable.
- `502`: provider response violated the structured-output contract.

Authentication is deliberately outside the current lab scope and is mandatory before exposing document or review endpoints publicly.
