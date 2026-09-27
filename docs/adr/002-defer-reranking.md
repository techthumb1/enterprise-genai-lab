# ADR 002: Defer Reranking

- Status: Accepted
- Date: 2026-09-27

## Context

The structured vector run achieved Recall@3 and Recall@5 of 1.0 with MRR 0.95. Hybrid RRF did not improve the measured result, and there were no hybrid misses at three.

## Decision

Use structured vector retrieval as the governed-answer default. Retain lexical and RRF implementations for evaluation, but do not add a cross-encoder or LLM reranker yet.

## Consequences

- lower latency, cost, and operational complexity;
- fewer model dependencies and failure modes;
- reranking remains available as a future experiment when a broader benchmark exposes a measurable ranking problem.
