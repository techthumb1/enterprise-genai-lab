# Deployment

## Configuration

Copy `.env.example` to a local `.env` and replace placeholders locally. Never commit `.env`, API keys, database passwords, cloud credentials, tokens, private keys, or exported provider responses containing sensitive documents.

Production requires `DATABASE_URL`. Provider-backed answer generation also requires `OPENAI_API_KEY`. Optional provider comparison uses `ANTHROPIC_API_KEY`.

The browser bundle must never contain any of these values. It uses relative same-origin HTTP calls and requires no environment-injected secret or public API key.

## Local stack

```bash
docker compose up -d db
uv sync --locked --group dev
uv run alembic upgrade head
npm --prefix ui ci
npm --prefix ui run build
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000`. For frontend hot reload, replace the build step with `npm --prefix ui run dev` in a second terminal; the Vite development server proxies `/api`, `/health`, and `/ready` to port 8000.

Readiness is false until PostgreSQL is reachable:

```bash
curl --fail http://localhost:8000/health
curl --fail http://localhost:8000/ready
```

## Container build

The Dockerfile uses a Node 24 build stage for the interface and a Python 3.12 runtime stage for the API. Only `ui/dist` is copied from the frontend stage; `node_modules`, source maps, local environment files, tests, and documentation are excluded from the runtime image.

```bash
docker build -t enterprise-genai-lab .
docker run --rm -p 8000:8000 --env-file .env enterprise-genai-lab
```

Apply Alembic migrations as a release step before starting new application replicas. Do not bake `.env` or cloud credentials into an image.

## Migration sequence

1. `8841142943bc`: documents, chunks, embeddings.
2. `ab8e0275ae7b`: immutable processing runs and chunk linkage.
3. `c4d5e6f7a8b9`: persisted human reviews and decision lifecycle.

Apply migrations before serving a revision that references the new schema. Use a restricted application role for normal runtime access and a separate migration role for DDL.

The local pgvector container provisions the `vector` extension through `docker/postgres/init.sql`. Managed PostgreSQL deployments must provision that extension with an authorized administrative/migration identity before the first schema migration.

## Production hardening checklist

- authenticate callers and authorize processing runs;
- authorize review access and bind reviewer identity to the session;
- protect the full review queue because it contains candidate answers and evidence text;
- set browser security headers and a restrictive content security policy;
- set request/body limits and rate limits;
- configure CORS explicitly;
- use managed secret storage and rotation;
- encrypt database storage and backups;
- define document retention/deletion policy;
- export OpenTelemetry to an approved sink with redaction;
- run PostgreSQL integration tests against the release schema;
- back up before migrations and rehearse restoration;
- pin approved provider models and evaluate before changing them.

This repository demonstrates the architecture; it does not claim those environment-specific controls are already supplied by every deployment.
