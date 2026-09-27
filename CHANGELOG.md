# Changelog

## 2026-09-27

- Added a responsive React 19/TypeScript answer workbench and human-review console.
- Added safe processing-run discovery and status-filtered review queue APIs.
- Added FastAPI static frontend delivery, a multi-stage Node/Python container build, and frontend CI gates.
- Restored technology badges and refreshed README, API, architecture, governance, deployment, observability, and security documentation.
- Added typed LangGraph orchestration for retrieval, structured generation, verification, risk routing, release, abstention, and human review.
- Added deterministic `allow`, `abstain`, and `human_review` policy.
- Added persisted review records, single-decision lifecycle, SQLAlchemy repository, and Alembic migration.
- Added governed answer and review APIs.
- Added Anthropic structured-generation adapter and provider-comparison evaluation harness.
- Added workflow observability metadata without raw content logging.
- Made database engine creation lazy so non-database unit tests and health imports do not require local credentials.
- Added CI, dependency updates, credential exclusions, security guidance, architecture/evaluation/API documentation, ADRs, and article draft.

## 2026-09-26

- Added deterministic parsing, provenance, fixed-window chunking, versioned processing runs, and idempotent persistence.
- Added embedding services, lexical/vector retrieval, RRF fusion, and processing-run isolation.
- Added the source-span-based retrieval benchmark and retained baseline/structured experiment.
- Added provider-independent grounded-generation contracts, OpenAI structured output, citation verification, explicit abstention, and the real-provider demonstration script.

## 2026-09-25

- Established the FastAPI, Pydantic, PostgreSQL 18, pgvector, SQLAlchemy, Alembic, Logfire/OpenTelemetry, Ruff, mypy, and pytest foundation.
