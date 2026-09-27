# Building an Evaluation-First Enterprise RAG System: From Raw Documents to Governed AI Decisions

Most RAG demonstrations stop when a model produces a plausible answer. Enterprise systems begin at the harder questions: which source representation produced the evidence, can the retrieval result be reproduced, did the model cite only what it saw, what happens when support is insufficient, and who approves a high-risk response?

This project started with a deliberately narrow rule: deterministic primitives first, measurements second, orchestration third.

## Source identity is not processing identity

A source document is deduplicated by checksum, but parsing and chunking strategies evolve. Treating chunks as permanent properties of the document would erase the experimental history. The persistence model therefore separates `Document` from `DocumentProcessingRun`. Each run records parser, normalization, chunker, version, and configuration, and each chunk points to the run that produced it.

That distinction made a controlled experiment possible. The same biomedical source was retained as a two-chunk plain-text baseline and an eight-chunk section-aware candidate. Both used the same fixed-window chunker; only representation changed.

## Measure retrieval before buying complexity

A ten-question dataset used original source spans as relevance labels, avoiding labels tied to either run's chunk UUIDs. The structured vector run reached Recall@3 and Recall@5 of 1.0 with MRR 0.95. Hybrid RRF produced the same result and no hybrid misses at three.

The important outcome was not a new component. It was the decision not to add one. A reranker would add latency, cost, and failure modes without correcting a measured problem.

## Model output is a candidate, not a decision

Generation uses a provider protocol and a structured `GroundedAnswer` contract. Only retrieved evidence enters the provider context. The result remains a `candidate_answer` until deterministic verification confirms that a normal answer has citations, every citation was supplied, and none are duplicated.

If a model fabricates a chunk ID, the candidate remains available for audit but the `final_answer` becomes an abstention. If the provider is unavailable, the system reports an operational failure rather than pretending the evidence was insufficient.

## LangGraph arrived after the primitives

Once retrieval, generation, verification, and abstention were independently testable, LangGraph became useful. Its typed state coordinates retrieval, context assembly, generation, verification, risk routing, finalization, abstention, and human review. It does not contain the SQL query, citation rules, or persistence policy.

This keeps the graph readable and the important rules usable outside the graph.

## Governance needs explicit states

The initial risk gate has three outcomes: allow, abstain, and human review. It uses explicit system facts rather than an invented confidence percentage. A valid standard-risk answer can be released. Failed grounding abstains. A valid high-risk candidate is persisted for review and is not released.

Reviews preserve the candidate, evidence snapshot, reason, reviewer identity, comment, status, and timestamps. A pending review may be decided once, which makes concurrent decisions visible instead of silently overwriting history.

## What the benchmark does—and does not—prove

The current results show that the architecture can preserve processing history, measure representation changes, retrieve within an experiment boundary, enforce citation IDs, route risk deterministically, and retain human decisions. The single-document benchmark does not prove production-scale retrieval quality, semantic factuality, or regulatory compliance.

The next meaningful experiments are claim-to-evidence entailment, prompt-injection quarantine, richer document formats, authenticated policy-derived risk tiers, and usage-normalized provider comparisons. Each should enter with a dataset and acceptance threshold, not because it is fashionable.

That is the larger lesson: trustworthy GenAI is less about assembling the maximum number of AI components and more about making every decision boundary measurable, reproducible, and reviewable.
