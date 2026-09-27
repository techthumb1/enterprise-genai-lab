# Observability

Logging is configured once in `app/core/logging.py` and bridges standard Python logging into Logfire/OpenTelemetry. Workflow nodes record operational metadata at useful boundaries.

## Recorded fields

- workflow and processing-run IDs;
- retrieval mode and result count;
- provider and model;
- retrieval/generation duration;
- provider abstention;
- grounding result;
- risk tier and disposition.

## Excluded fields

- API keys, credentials, and connection strings;
- raw questions, prompts, and evidence content;
- full model responses;
- unnecessary personal or regulated data.

Local configuration uses `send_to_logfire=False`. A deployment may enable an approved exporter only after retention, access, redaction, and data-residency requirements are defined.

Token and cost metadata are not logged because the current provider protocol does not yet normalize usage consistently. Add those fields only with explicit typed metadata and tests.
