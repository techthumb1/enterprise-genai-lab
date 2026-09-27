import { useEffect, useMemo, useState, type FormEvent } from "react";

import { api } from "../api";
import {
  ArrowIcon,
  CheckIcon,
  ClockIcon,
  DatabaseIcon,
  ShieldIcon,
  SparkIcon,
} from "../components/Icons";
import { formatDate, formatDisposition, shortId } from "../format";
import type { AnswerResponse, ProcessingRun, RiskTier } from "../types";

interface AnswerWorkbenchProps {
  onOpenReview: (reviewId: string) => void;
}

const sampleQuestions = [
  "What governance controls are described in this document?",
  "Summarize the evidence-backed implementation decisions.",
  "What requires human review?",
];

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "An unexpected error occurred.";
}

export function AnswerWorkbench({ onOpenReview }: AnswerWorkbenchProps) {
  const [runs, setRuns] = useState<ProcessingRun[]>([]);
  const [runsLoading, setRunsLoading] = useState(true);
  const [runsError, setRunsError] = useState<string | null>(null);
  const [selectedRunId, setSelectedRunId] = useState("");
  const [query, setQuery] = useState("");
  const [riskTier, setRiskTier] = useState<RiskTier>("standard");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<AnswerResponse | null>(null);
  const [elapsedMs, setElapsedMs] = useState<number | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    api
      .processingRuns()
      .then((items) => {
        if (!active) return;
        setRuns(items);
        setSelectedRunId((current) => current || items[0]?.id || "");
        setRunsError(null);
      })
      .catch((error: unknown) => {
        if (active) setRunsError(errorMessage(error));
      })
      .finally(() => {
        if (active) setRunsLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  const selectedRun = useMemo(
    () => runs.find((run) => run.id === selectedRunId) ?? null,
    [runs, selectedRunId],
  );

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const input = event.currentTarget.elements.namedItem("document") as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) {
      setUploadError("Document exceeds the 2 MB limit.");
      return;
    }
    setUploading(true);
    setUploadError(null);
    setUploadMessage(null);
    try {
      const uploaded = await api.uploadDocument(file);
      const items = await api.processingRuns();
      setRuns(items);
      setSelectedRunId(uploaded.processing_run_id);
      setRunsError(null);
      setUploadMessage(`${file.name} indexed with ${uploaded.chunk_count} chunks. Select it and ask a question.`);
      input.value = "";
    } catch (error: unknown) {
      setUploadError(errorMessage(error));
    } finally {
      setUploading(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedQuery = query.trim();
    if (!normalizedQuery || !selectedRunId) return;

    setSubmitting(true);
    setSubmitError(null);
    const started = performance.now();

    try {
      const answer = await api.answer({
        query: normalizedQuery,
        processing_run_id: selectedRunId,
        risk_tier: riskTier,
      });
      setResult(answer);
      setElapsedMs(performance.now() - started);
    } catch (error: unknown) {
      setSubmitError(errorMessage(error));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page-shell">
      <section className="page-heading">
        <div>
          <span className="eyebrow">Governed retrieval + generation</span>
          <h1>Answer workbench</h1>
          <p>
            Ask against one immutable processing run. Every response is checked
            for evidence, citations, and release risk before it reaches you.
          </p>
        </div>
        <div className="policy-chip">
          <ShieldIcon />
          Policy gates active
        </div>
      </section>

      <div className="workbench-grid">
        <section className="panel query-panel" aria-labelledby="query-title">
          <div className="panel-heading">
            <div className="step-number">01</div>
            <div>
              <h2 id="query-title">Frame the question</h2>
              <p>Select a source representation and the required risk tier.</p>
            </div>
          </div>

          <form className="upload-form" onSubmit={handleUpload}>
            <label className="field-label" htmlFor="document">Add a document</label>
            <p>Upload UTF-8 .txt or .md, up to 2 MB. Indexing uses the configured provider.</p>
            <div className="upload-controls">
              <input id="document" name="document" type="file" accept=".txt,.md,.markdown,text/plain,text/markdown" required />
              <button type="submit" disabled={uploading}>
                {uploading ? "Indexing…" : "Upload and index"}
              </button>
            </div>
            {uploadError && <div className="inline-alert error" role="alert">{uploadError}</div>}
            {uploadMessage && <div className="inline-alert" role="status">{uploadMessage}</div>}
          </form>

          <form onSubmit={handleSubmit}>
            <label className="field-label" htmlFor="processing-run">
              Processing run
            </label>
            <div className="select-wrap">
              <DatabaseIcon />
              <select
                id="processing-run"
                value={selectedRunId}
                onChange={(event) => setSelectedRunId(event.target.value)}
                disabled={runsLoading || runs.length === 0}
                required
              >
                {runsLoading && <option value="">Loading processing runs…</option>}
                {!runsLoading && runs.length === 0 && (
                  <option value="">No retrieval-ready runs</option>
                )}
                {runs.map((run) => (
                  <option key={run.id} value={run.id}>
                    {run.filename} · {run.chunk_count} chunks
                  </option>
                ))}
              </select>
            </div>

            {runsError && <div className="inline-alert error">{runsError}</div>}

            {selectedRun && (
              <div className="run-summary" aria-label="Selected processing run">
                <span>
                  <strong>{selectedRun.chunk_count}</strong> chunks
                </span>
                <span>
                  <strong>{selectedRun.parser_name}</strong> parser
                </span>
                <span>
                  <strong>{selectedRun.embedding_model}</strong> embeddings
                </span>
                <span title={selectedRun.id}>
                  Run <strong>{shortId(selectedRun.id)}</strong>
                </span>
              </div>
            )}

            <div className="field-row">
              <label className="field-label" htmlFor="question">
                Question
              </label>
              <span className="character-count">{query.length} / 4,000</span>
            </div>
            <textarea
              id="question"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Ask a specific question that can be answered from the selected evidence…"
              rows={7}
              maxLength={4000}
              required
            />

            <div className="prompt-suggestions" aria-label="Example questions">
              {sampleQuestions.map((question) => (
                <button
                  key={question}
                  type="button"
                  onClick={() => setQuery(question)}
                >
                  {question}
                </button>
              ))}
            </div>

            <fieldset className="risk-fieldset">
              <legend className="field-label">Risk tier</legend>
              <div className="risk-options">
                <label className={riskTier === "standard" ? "selected" : ""}>
                  <input
                    type="radio"
                    name="risk-tier"
                    value="standard"
                    checked={riskTier === "standard"}
                    onChange={() => setRiskTier("standard")}
                  />
                  <span>
                    <strong>Standard</strong>
                    <small>Release when grounding checks pass</small>
                  </span>
                </label>
                <label className={riskTier === "high" ? "selected" : ""}>
                  <input
                    type="radio"
                    name="risk-tier"
                    value="high"
                    checked={riskTier === "high"}
                    onChange={() => setRiskTier("high")}
                  />
                  <span>
                    <strong>High</strong>
                    <small>Always route grounded output to review</small>
                  </span>
                </label>
              </div>
            </fieldset>

            {submitError && (
              <div className="inline-alert error" role="alert">
                {submitError}
              </div>
            )}

            <button
              className="primary-button submit-button"
              type="submit"
              disabled={submitting || !selectedRunId || !query.trim()}
            >
              {submitting ? (
                <>
                  <span className="spinner" /> Running governed workflow…
                </>
              ) : (
                <>
                  Generate governed answer <ArrowIcon />
                </>
              )}
            </button>
          </form>
        </section>

        <section className="panel result-panel" aria-labelledby="result-title">
          <div className="panel-heading compact">
            <div className="step-number">02</div>
            <div>
              <h2 id="result-title">Governed result</h2>
              <p>Only policy-approved output is shown here.</p>
            </div>
          </div>

          {result ? (
            <AnswerResult
              result={result}
              elapsedMs={elapsedMs}
              onOpenReview={onOpenReview}
            />
          ) : (
            <div className="result-empty">
              <div className="empty-illustration">
                <SparkIcon />
                <span />
                <ShieldIcon />
              </div>
              <h3>Ready for a governed answer</h3>
              <p>
                The workflow retrieves bounded evidence, generates a structured
                candidate, verifies every citation, and applies the risk gate.
              </p>
              <ol className="workflow-preview">
                <li>Retrieve evidence</li>
                <li>Verify grounding</li>
                <li>Apply policy</li>
              </ol>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

interface AnswerResultProps {
  result: AnswerResponse;
  elapsedMs: number | null;
  onOpenReview: (reviewId: string) => void;
}

function AnswerResult({ result, elapsedMs, onOpenReview }: AnswerResultProps) {
  const disposition = result.risk.disposition;
  const statusLabel =
    disposition === "allow"
      ? "Released"
      : disposition === "human_review"
        ? "Review required"
        : "Abstained";

  return (
    <div className="answer-result" aria-live="polite">
      <div className="result-status-row">
        <span className={`outcome-badge ${disposition}`}>
          {disposition === "allow" ? <CheckIcon /> : <ShieldIcon />}
          {statusLabel}
        </span>
        {elapsedMs !== null && (
          <span className="latency">
            <ClockIcon /> {(elapsedMs / 1000).toFixed(2)}s
          </span>
        )}
      </div>

      <div className="answer-copy">
        <span className="section-kicker">Final answer</span>
        {result.final_answer.abstained ? (
          <p className="abstention-copy">
            {result.final_answer.abstention_reason ?? "The workflow abstained."}
          </p>
        ) : (
          <p>{result.final_answer.answer}</p>
        )}
      </div>

      {result.final_answer.citations.length > 0 && (
        <div className="citation-block">
          <span className="section-kicker">
            Citations · {result.final_answer.citations.length}
          </span>
          <div className="citation-list">
            {result.final_answer.citations.map((citation, index) => (
              <span key={citation.chunk_id} title={citation.chunk_id}>
                [{index + 1}] {shortId(citation.chunk_id)}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="decision-card">
        <div>
          <span className="section-kicker">Policy decision</span>
          <strong>{formatDisposition(result.risk.disposition)}</strong>
          <p>{result.risk.reason}</p>
        </div>
        <div className="verification-mark">
          {result.verification.valid ? <CheckIcon /> : <ShieldIcon />}
          <span>
            <strong>
              {result.verification.valid ? "Grounding verified" : "Verification failed"}
            </strong>
            <small>{result.retrieved_evidence_count} evidence chunks retrieved</small>
          </span>
        </div>
      </div>

      {result.verification.errors.length > 0 && (
        <ul className="verification-errors">
          {result.verification.errors.map((error) => (
            <li key={error}>{error}</li>
          ))}
        </ul>
      )}

      {result.review_id && (
        <button
          type="button"
          className="review-callout"
          onClick={() => onOpenReview(result.review_id as string)}
        >
          <span>
            <strong>Human review created</strong>
            <small>Review {shortId(result.review_id)}</small>
          </span>
          Open review <ArrowIcon />
        </button>
      )}

      <dl className="result-metadata">
        <div>
          <dt>Provider</dt>
          <dd>{result.provider}</dd>
        </div>
        <div>
          <dt>Model</dt>
          <dd>{result.model}</dd>
        </div>
        <div>
          <dt>Workflow</dt>
          <dd title={result.workflow_id}>{shortId(result.workflow_id)}</dd>
        </div>
        <div>
          <dt>Completed</dt>
          <dd>{formatDate(new Date().toISOString())}</dd>
        </div>
      </dl>
    </div>
  );
}
