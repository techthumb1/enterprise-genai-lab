# ADR 001: Deterministic Primitives Before Orchestration

- Status: Accepted
- Date: 2026-09-27

## Context

Retrieval, verification, risk rules, and persistence must be usable and testable without reconstructing graph execution state.

## Decision

Implement those behaviors as typed application services and pure functions. LangGraph coordinates their order and conditional branches but does not own their algorithms or persistence queries.

## Consequences

- domain rules have fast deterministic unit tests;
- graph nodes remain small;
- provider and API integrations can reuse contracts;
- workflow state is inspectable;
- changes may require explicit wiring rather than hiding behavior in a general-purpose agent node.
