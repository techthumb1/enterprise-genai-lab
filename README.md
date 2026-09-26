<div align="center">

# Enterprise AI Risk & Document Intelligence

**Production-oriented GenAI architecture for document intelligence, retrieval, evaluation, governance, and human review.**

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Modern_Async_API-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-4169E1?logo=postgresql&logoColor=white)
![pgvector](https://img.shields.io/badge/pgvector-Vector_Search-4169E1)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.x-D71F00)
![LangGraph](https://img.shields.io/badge/LangGraph-1.x-111111)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?logo=pydantic&logoColor=white)
![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-Observability-000000?logo=opentelemetry&logoColor=white)
![Ruff](https://img.shields.io/badge/Ruff-Linting-D7FF64?logo=ruff&logoColor=111111)
![mypy](https://img.shields.io/badge/mypy-Strict_Typing-2A6DB2)

</div>

---

## Overview

**Enterprise AI Risk & Document Intelligence** is a hands-on reference implementation for building modern enterprise Generative AI systems beyond basic chatbot or prompt-wrapper patterns.

The project focuses on the engineering concerns that become critical when AI systems operate over enterprise documents and must produce outputs that are **retrievable, observable, explainable, evaluable, and governable**.

The target architecture combines:

- document intelligence and structured ingestion
- retrieval-augmented generation
- hybrid and vector retrieval
- model and retrieval evaluation
- typed AI workflows
- evidence and citation verification
- human-in-the-loop review
- AI risk and governance controls
- end-to-end observability
- production-oriented API and persistence patterns

The project is intentionally **evaluation-first**. More advanced AI techniques are added only when they demonstrate measurable improvement over simpler baselines.

---

## Current Engineering Status

### Foundation Complete

The initial production foundation is implemented and validated.

| Capability | Status |
|---|---|
| Python 3.12 environment managed with `uv` | ✅ |
| FastAPI application foundation | ✅ |
| Pydantic v2 configuration and validation | ✅ |
| PostgreSQL 18.6 | ✅ |
| Native PostgreSQL UUIDv7 identifiers | ✅ |
| pgvector extension | ✅ |
| SQLAlchemy 2.x asynchronous persistence | ✅ |
| `asyncpg` database driver | ✅ |
| Alembic asynchronous migrations | ✅ |
| Dedicated least-privilege application database role | ✅ |
| Health and database readiness checks | ✅ |
| Ruff static analysis | ✅ |
| Strict mypy type checking | ✅ |
| Modern dependency baseline | ✅ |

### Initial Persistence Model

The first migration establishes the core document-intelligence persistence layer:

- `documents`
- `document_chunks`
- `chunk_embeddings`

The schema currently supports:

- PostgreSQL-native UUIDv7 primary keys
- SHA-256 document deduplication
- JSONB source and chunk metadata
- document-to-chunk relationships
- cascading cleanup
- model-aware embedding records
- pgvector-backed embedding storage
- multiple embedding providers and models per chunk

Embedding dimensionality is intentionally **not yet fixed at the database level**. The canonical embedding model and ANN indexing strategy will be selected through retrieval evaluation rather than assumed in advance.

---

## Architecture Direction

The system is being developed around the following flow:

```text
Enterprise Documents
        │
        ▼
Document Intelligence
        │
        ├── Parsing
        ├── Normalization
        ├── Provenance
        └── Deduplication
        │
        ▼
Chunking
        │
        ▼
PostgreSQL 18 + pgvector
        │
        ├── Full-Text Retrieval
        ├── Dense Retrieval
        ├── Metadata Filtering
        └── Vector Search
        │
        ▼
Hybrid Retrieval
        │
        ├── Reciprocal Rank Fusion
        └── Reranking
        │
        ▼
LLM Generation
        │
        ├── Structured Outputs
        ├── Evidence Attribution
        └── Model Routing
        │
        ▼
Verification & Evaluation
        │
        ├── Grounding
        ├── Citation Validation
        ├── Confidence
        └── Risk Assessment
        │
        ▼
LangGraph Workflow
        │
        ├── Conditional Routing
        ├── Retry / Abstention
        └── Human Review
        │
        ▼
FastAPI
        │
        ▼
OpenTelemetry / Logfire
```

---

## Core Engineering Principles

### Evaluation Before Optimization

The project establishes measurable baselines before introducing more complex retrieval or agentic techniques.

Examples include:

- exact vector search before approximate nearest-neighbor search
- lexical retrieval before hybrid retrieval
- deterministic chunking before semantic chunking
- baseline retrieval before reranking
- provider/model comparisons before model selection
- measurable quality improvements before adding architectural complexity

### Evidence-First Generation

Retrieved content is treated as **untrusted evidence**, not executable instruction.

The planned governance layer includes:

- evidence attribution
- citation enforcement
- claim verification
- grounding checks
- prompt-injection defenses
- abstention behavior
- risk thresholds
- human approval workflows

### Provider Independence

Model providers will sit behind internal application interfaces.

The system is designed to support multiple providers while preventing orchestration, persistence, retrieval, or governance logic from becoming tightly coupled to a single vendor SDK.

### Typed Boundaries

Pydantic and SQLAlchemy typed models define explicit boundaries between:

- APIs
- persistence
- retrieval
- workflow state
- model outputs
- evaluations
- human-review actions

### Least Privilege

The application connects to PostgreSQL through a dedicated restricted database role rather than an administrative account.

Database extension provisioning and other privileged operations remain separate from normal application execution.

---

## Technology Stack

### Application

- **Python 3.12**
- **FastAPI**
- **Pydantic v2**
- **Pydantic Settings**
- **uv**

### AI / Orchestration

- **LangGraph 1.x**
- **OpenAI**
- **Anthropic**

Provider integrations will use structured outputs and typed internal contracts rather than arbitrary prose parsing.

### Persistence

- **PostgreSQL 18**
- **pgvector**
- **SQLAlchemy 2.x Async ORM**
- **asyncpg**
- **Alembic**

PostgreSQL 18-native `uuidv7()` is used for sortable distributed identifiers.

### Observability

Planned primary observability architecture:

- **Pydantic Logfire**
- **OpenTelemetry**

The objective is full workflow observability rather than application logging alone, including:

- HTTP requests
- document processing
- retrieval stages
- model calls
- tool calls
- workflow transitions
- latency
- token consumption
- evaluation results
- retries and failures

Sensitive document or prompt content will not be exported indiscriminately.

### Engineering Quality

- **Ruff**
- **mypy**
- **pytest**
- **pytest-asyncio**
- **pytest-cov**

Current application code passes Ruff and strict mypy validation.

---

## Document Intelligence Roadmap

The next phase implements the ingestion pipeline.

### Phase 1 — Deterministic Ingestion

- SHA-256 source hashing
- duplicate detection
- typed ingestion contracts
- source metadata
- provenance preservation
- TXT parsing
- Markdown parsing
- deterministic chunking
- persistence of documents and chunks

### Phase 2 — Rich Document Parsing

Planned evaluation of modern document-processing approaches for:

- PDF
- DOCX
- HTML
- structured documents
- complex layouts
- tables
- multimodal content

OCR and vision-based extraction will be introduced only where document characteristics require them.

---

## Retrieval Roadmap

Retrieval quality will be measured before production strategy is selected.

Planned progression:

1. PostgreSQL lexical/full-text baseline
2. exact dense vector retrieval
3. embedding model comparison
4. hybrid lexical + dense retrieval
5. Reciprocal Rank Fusion
6. metadata filtering
7. reranking
8. contextual retrieval experiments
9. approximate nearest-neighbor evaluation
10. production HNSW strategy

Approximate search will be compared against exact search so ANN recall loss can be measured rather than assumed acceptable.

---

## Evaluation Strategy

Evaluation is a first-class system component rather than a final testing step.

### Retrieval Metrics

Planned metrics include:

- Recall@K
- Precision@K
- Mean Reciprocal Rank
- nDCG
- context relevance
- latency
- storage requirements

### Generation Metrics

Planned evaluation includes:

- groundedness
- factual correctness
- citation correctness
- completeness
- hallucination rate
- structured-output compliance
- latency
- token usage
- cost

Evaluation datasets will be versioned to support regression testing as retrieval, prompts, models, and workflow behavior change.

---

## Agentic Workflow

LangGraph will be used as an orchestration layer rather than as the owner of core business logic.

The target workflow includes:

```text
Classify
   ↓
Retrieve Evidence
   ↓
Assess Evidence
   ↓
Analyze
   ↓
Verify Claims
   ↓
Confidence / Risk Gate
   │
   ├── Complete
   ├── Retry
   ├── Abstain
   └── Human Review
```

Planned capabilities include:

- typed workflow state
- conditional routing
- retry policies
- checkpointing
- interrupts
- human approval
- auditable workflow outcomes

---

## AI Risk & Governance

The project will explore controls appropriate for enterprise and regulated GenAI environments.

Planned areas include:

- prompt-injection resistance
- provenance-bound evidence
- evidence sufficiency
- claim-level verification
- citation validation
- model and prompt version tracking
- retrieval-version tracking
- risk-based routing
- abstention
- human review
- decision history
- auditability
- privacy-aware telemetry

The goal is not merely to produce an answer, but to preserve enough evidence and execution context to explain **how the system reached that answer**.

---

## Observability Goals

The intended trace hierarchy is:

```text
Request
 ├── Document Processing
 ├── Retrieval
 │    ├── Lexical Search
 │    ├── Vector Search
 │    ├── Fusion
 │    └── Reranking
 ├── Model Invocation
 ├── Verification
 ├── Risk Assessment
 └── Human Review
```

Telemetry will eventually capture appropriate metadata such as:

- request and workflow identifiers
- provider and model
- retrieval strategy
- candidates retrieved
- ranking stages
- latency
- tokens
- retries
- evaluation run
- execution outcome

---

## Development Philosophy

This repository intentionally avoids adding technologies simply because they are fashionable.

Potential techniques such as:

- semantic chunking
- contextual retrieval
- sparse embeddings
- late interaction / ColBERT
- multi-vector retrieval
- GraphRAG
- model routing
- DSPy
- PydanticAI
- MCP
- traditional ML risk classifiers

will be introduced as **measured experiments** where they solve a demonstrated problem.

The objective is to show not only how modern GenAI technologies are implemented, but how engineering teams can determine **when they should be used**.

---

## Current Validation

The current application foundation has successfully passed:

```bash
uv run ruff check app
```

```text
All checks passed!
```

and:

```bash
uv run mypy app
```

```text
Success: no issues found in 19 source files
```

Database connectivity has also been verified asynchronously from the application:

```text
Database ready: True
```

The first Alembic schema revision has been successfully applied to PostgreSQL 18.

---

## Project Direction

The next major milestones are:

**Document Intelligence → Retrieval Baselines → Retrieval Evaluation → Embeddings → Hybrid Search → Reranking → Structured Generation → Governance → LangGraph Orchestration → Human Review → Full AI Observability**

The final result is intended to serve as both a working system and a reference architecture for designing measurable, governable enterprise GenAI applications.