# Retrieval Evaluation

## Retained source

- File: `samples/2. Building KG Drug Discovery.txt`
- Document ID: `01a0dea1-1638-71e2-b041-a16f76f8e10a`
- SHA-256: `e0b923ee555103f0c9442db3000f6e68b99b5ffb0336e11fe777d7cdc221d8f6`

The document contains an introduction, six implementation steps, and a conclusion.

## Controlled representation experiment

| Variant | Processing run | Representation | Chunks |
| --- | --- | --- | ---: |
| Baseline | `01a0df9d-c34c-7d81-bcb4-9d1541d31518` | plain text + fixed token window | 2 |
| Structured | `01a0e025-2603-7dbe-a393-0b3b653d7d02` | section-aware text + same fixed token window | 8 |

The historical baseline must not be rewritten. Relevance labels use source spans rather than chunk UUIDs, allowing the same ten questions to evaluate different chunk boundaries.

## Results

| Run | Mode | R@1 | R@3 | R@5 | MRR |
| --- | --- | ---: | ---: | ---: | ---: |
| Baseline | lexical | 0.100 | 0.100 | 0.100 | 0.100 |
| Baseline | vector | 0.800 | 1.000 | 1.000 | 0.950 |
| Baseline | hybrid | 0.800 | 1.000 | 1.000 | 0.950 |
| Structured | lexical | 0.100 | 0.100 | 0.100 | 0.100 |
| Structured | vector | 0.850 | 1.000 | 1.000 | 0.950 |
| Structured | hybrid | 0.850 | 1.000 | 1.000 | 0.950 |

There were no hybrid misses at `k=3`. Vector retrieval over the structured representation is therefore the governed-answer default. Hybrid remains available but is not the default, and a reranker is deferred until evaluation reveals a failure it can address.

## Reproduce

```bash
uv run python -m scripts.evaluate_retrieval
```

This compact, single-document benchmark validates architectural plumbing and controlled comparisons. It is not evidence of performance over a production corpus; broader, adversarial, and domain-specific datasets are a planned extension.
