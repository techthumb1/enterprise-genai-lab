# Governance and Human Review

## Candidate versus final output

The model produces `candidate_answer`; the governed system produces `final_answer`. This boundary prevents a structurally valid model response from being treated as releasable before deterministic controls run.

| Condition | Outcome |
| --- | --- |
| No evidence | Abstain without calling the provider |
| Valid explicit provider abstention | Preserve abstention |
| Missing, duplicate, or unavailable citation | Preserve candidate for audit; final answer abstains |
| Verified standard-risk answer | Allow |
| Verified high-risk answer | Persist pending review; do not release candidate |
| Provider outage | Operational error, not abstention |

## Citation verification

The current verifier answers a narrow, deterministic question: did the model cite only evidence supplied in this request, without duplicates, and did a normal answer cite at least one chunk?

It does not claim that every sentence is semantically entailed by the cited text. Claim-level support checking is a separate planned evaluation and must not replace the deterministic allow-list check.

## Risk gate

The initial risk gate uses auditable categorical inputs. It deliberately avoids synthetic confidence scores:

- evidence exists;
- a candidate exists;
- citation verification passed;
- the provider abstained or answered;
- the caller-selected workflow risk tier is standard or high.

`risk_tier` is a demonstration input. A production deployment should derive it from authenticated workflow policy, document classification, jurisdiction, and user authority rather than trust arbitrary client input.

## Human review record

A pending review stores workflow and review IDs, routing reason, candidate answer, evidence snapshot and citations, status, reviewer identity/comment, and timestamps.

Decision updates only succeed while status is `pending`, preventing two reviewers from silently overwriting one another.

## Review console

The review console makes the existing lifecycle operable without changing its authority model. Reviewers can filter pending, approved, and rejected records; compare an unreleased candidate with its captured evidence; see which chunks were cited; and approve or reject only after entering both reviewer identity and rationale.

The UI does not release a candidate directly or bypass server checks. A decision still passes through the concurrency-safe API update, and a stale second decision receives `409`. The browser-supplied reviewer ID is a lab input; production must derive verified reviewer identity and permissions from an authenticated session.

## Security boundaries

- Governed answer responses do not expose raw evidence or unreleased candidates.
- Review responses expose both by design and therefore require stricter authorization.
- Logs contain identifiers, counts, timing, model metadata, and outcomes—not API keys or raw prompts.
- Secrets are loaded through `SecretStr` settings and local environment variables.
- Review endpoints require an authentication/authorization layer before public production use.
- Evidence is untrusted data. Provider instructions state that only the application contract, not document content, controls behavior.

Passing current controls means citation IDs were valid and routing policy was followed. It is not a regulatory certification, factual guarantee, or substitute for subject-matter review.
