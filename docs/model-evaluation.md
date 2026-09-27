# Model and Generation Evaluation

## Purpose

Generation evaluation compares providers over identical `GenerationRequest` evidence. Retrieval is performed once per case so a provider is not advantaged by a different context set.

The compact evaluation reports only observed properties:

- structured-output success;
- deterministic grounding-verification pass rate;
- expected abstention accuracy;
- citation count;
- operational-error rate;
- latency.

Token and cost metrics are intentionally absent until every evaluated adapter exposes comparable usage metadata. No fabricated quality or confidence score is reported.

## Run

```bash
uv run python -m scripts.evaluate_generation
uv run python -m scripts.evaluate_generation --include-anthropic
```

Required configuration:

- `DATABASE_URL` for the retained benchmark data;
- `OPENAI_API_KEY` for query embeddings and OpenAI generation;
- `ANTHROPIC_API_KEY` only for the optional comparison.

The script never prints keys and sends only selected evidence to providers. Results are emitted as JSON for later comparison. Live calls are manual and excluded from pytest/CI.

## Cases

The starter suite includes supported questions about homogeneous graph conversion and negative sampling plus a deliberately unsupported clinical-trial question that should abstain. Expand the suite only with reviewed expected behavior and retained evidence snapshots.

`grounding_pass_rate` means citation-policy compliance, not semantic truth. A provider decision should combine these metrics with repeated runs, usage/cost data, and claim-level evaluation once that evaluator is validated.
