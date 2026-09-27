# User Interface

## Purpose

The interface is a lightweight operational layer over the governed API. It is intentionally not a general chat client, document manager, analytics suite, or administration console. Policy decisions remain on the server.

| Surface | Purpose | Data shown |
| --- | --- | --- |
| Answer workbench | Ask one question against one immutable, retrieval-ready processing run | Safe run metadata, governed final answer, citations, verification, routing, model metadata, timing |
| Review console | Decide persisted high-risk candidates | Routing reason, unreleased candidate, evidence snapshot, cited chunks, decision status, reviewer rationale |

## Answer workbench

The workbench loads `GET /api/processing-runs` and permits selection only from runs fully embedded for the configured provider/model. The request includes a question, processing-run ID, and demonstration risk tier. The result renders the server's `final_answer`; it never attempts to reconstruct a candidate from browser state.

A standard-risk answer can be released only when deterministic grounding checks pass. A high-risk, otherwise-valid answer shows its pending-review ID and links to the review console. Abstentions display the server-recorded reason.

## Review console

The console queries reviews by `pending`, `approved`, or `rejected` status. Pending records present the candidate beside the exact evidence snapshot captured by the workflow. Cited chunks are marked for inspection.

Approve and reject actions require a reviewer ID and rationale. The API remains responsible for validating the transition and preventing repeated or concurrent decisions. A production identity provider must replace the user-entered reviewer ID and authorize both queue access and decisions.

## Local development

Run FastAPI on port 8000:

```bash
uv run uvicorn app.main:app --reload
```

Run Vite with hot reload in another terminal:

```bash
npm --prefix ui ci
npm --prefix ui run dev
```

Open `http://localhost:5173`. Vite proxies relative `/api`, `/health`, and `/ready` calls to FastAPI.

For the integrated production-style path:

```bash
npm --prefix ui run build
uv run uvicorn app.main:app
```

Open `http://localhost:8000`. FastAPI serves `ui/dist` after matching explicit system and API routes.

## Verification

```bash
npm --prefix ui run lint
npm --prefix ui run test
npm --prefix ui run build
```

The test suite verifies navigation and the credential-free API client. The TypeScript compiler and Vite production build run as part of `npm --prefix ui run check` and CI.

## Security and privacy boundary

- The bundle contains no provider key, database URL, cloud credential, or secret configuration.
- API requests are relative and same-origin.
- Questions, answers, evidence, and reviewer comments are not stored in browser local storage.
- General answer responses omit evidence text and unreleased candidates.
- Review responses contain sensitive evidence and require authentication and authorization before public use.
- Reviewer identity entered in the lab UI is an audit field, not proof of identity.
