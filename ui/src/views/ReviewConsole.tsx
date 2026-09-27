import {
  useEffect,
  useMemo,
  useState,
  type FormEvent,
} from "react";

import { api } from "../api";
import {
  CheckIcon,
  ClockIcon,
  CloseIcon,
  QuoteIcon,
  RefreshIcon,
  ReviewIcon,
  ShieldIcon,
} from "../components/Icons";
import { formatDate, shortId } from "../format";
import type {
  ReviewDecisionStatus,
  ReviewRecord,
  ReviewStatus,
} from "../types";

interface ReviewConsoleProps {
  requestedReviewId: string | null;
}

const statusLabels: Record<ReviewStatus, string> = {
  pending: "Pending",
  approved: "Approved",
  rejected: "Rejected",
};

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "An unexpected error occurred.";
}

export function ReviewConsole({ requestedReviewId }: ReviewConsoleProps) {
  const [statusFilter, setStatusFilter] = useState<ReviewStatus>("pending");
  const [reviews, setReviews] = useState<ReviewRecord[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(
    requestedReviewId,
  );
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    api
      .reviews(statusFilter)
      .then((records) => {
        if (!active) return;
        setReviews(records);
        setSelectedId((current) => {
          const preferred = requestedReviewId ?? current;
          return (
            records.find((review) => review.id === preferred)?.id ??
            records[0]?.id ??
            null
          );
        });
      })
      .catch((error: unknown) => {
        if (active) setLoadError(errorMessage(error));
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [requestedReviewId, statusFilter]);

  const selectedReview = useMemo(
    () => reviews.find((review) => review.id === selectedId) ?? null,
    [reviews, selectedId],
  );

  function handleStatusChange(status: ReviewStatus) {
    setSuccessMessage(null);
    setLoadError(null);
    setLoading(true);
    setSelectedId(null);
    setStatusFilter(status);
  }

  async function refreshReviews() {
    setLoading(true);
    setLoadError(null);
    try {
      const records = await api.reviews(statusFilter);
      setReviews(records);
      setSelectedId((current) =>
        records.some((review) => review.id === current)
          ? current
          : (records[0]?.id ?? null),
      );
    } catch (error: unknown) {
      setLoadError(errorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  function handleDecision(decided: ReviewRecord) {
    const remaining = reviews.filter((review) => review.id !== decided.id);
    setReviews(remaining);
    setSelectedId(remaining[0]?.id ?? null);
    setSuccessMessage(
      `Review ${shortId(decided.id)} was ${decided.status}. The rationale is stored with the decision.`,
    );
  }

  return (
    <div className="page-shell review-page">
      <section className="page-heading">
        <div>
          <span className="eyebrow">Human-in-the-loop governance</span>
          <h1>Review console</h1>
          <p>
            Inspect the candidate beside its evidence snapshot, then record an
            accountable approval or rejection with mandatory rationale.
          </p>
        </div>
        <button
          type="button"
          className="secondary-button"
          onClick={() => void refreshReviews()}
          disabled={loading}
        >
          <RefreshIcon className={loading ? "spin" : ""} />
          Refresh queue
        </button>
      </section>

      <div className="review-toolbar">
        <div className="status-tabs" aria-label="Review status filter">
          {(Object.keys(statusLabels) as ReviewStatus[]).map((status) => (
            <button
              key={status}
              type="button"
              className={statusFilter === status ? "active" : ""}
              onClick={() => handleStatusChange(status)}
            >
              {statusLabels[status]}
              {status === statusFilter && <span>{reviews.length}</span>}
            </button>
          ))}
        </div>
        <span className="evidence-notice">
          <ShieldIcon /> Evidence is visible only inside the review surface
        </span>
      </div>

      {successMessage && (
        <div className="inline-alert success" role="status">
          <CheckIcon /> {successMessage}
        </div>
      )}
      {loadError && (
        <div className="inline-alert error" role="alert">
          {loadError}
        </div>
      )}

      <div className="review-grid">
        <aside className="review-queue panel" aria-label="Review queue">
          <div className="queue-header">
            <span>{statusLabels[statusFilter]} queue</span>
            <strong>{reviews.length}</strong>
          </div>

          {loading ? (
            <div className="queue-loading" aria-label="Loading reviews">
              <span />
              <span />
              <span />
            </div>
          ) : reviews.length === 0 ? (
            <div className="queue-empty">
              <ReviewIcon />
              <strong>No {statusFilter} reviews</strong>
              <p>
                {statusFilter === "pending"
                  ? "High-risk grounded answers will appear here."
                  : `No ${statusFilter} decisions are available.`}
              </p>
            </div>
          ) : (
            <div className="queue-list">
              {reviews.map((review) => (
                <button
                  type="button"
                  key={review.id}
                  className={review.id === selectedId ? "selected" : ""}
                  onClick={() => setSelectedId(review.id)}
                >
                  <span className={`queue-status ${review.status}`} />
                  <span className="queue-item-copy">
                    <strong>{review.candidate_answer.answer}</strong>
                    <small>{review.reason}</small>
                    <span>
                      <ClockIcon /> {formatDate(review.created_at)}
                    </span>
                  </span>
                </button>
              ))}
            </div>
          )}
        </aside>

        <section className="review-detail panel" aria-label="Selected review">
          {selectedReview ? (
            <ReviewDetail
              key={selectedReview.id}
              review={selectedReview}
              onDecision={handleDecision}
            />
          ) : (
            <div className="detail-empty">
              <ReviewIcon />
              <h2>Select a review</h2>
              <p>Choose an item from the queue to inspect its complete record.</p>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

interface ReviewDetailProps {
  review: ReviewRecord;
  onDecision: (review: ReviewRecord) => void;
}

function ReviewDetail({ review, onDecision }: ReviewDetailProps) {
  const [reviewerId, setReviewerId] = useState("");
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [decisionError, setDecisionError] = useState<string | null>(null);
  const citedChunkIds = new Set(
    review.candidate_answer.citations.map((citation) => citation.chunk_id),
  );

  async function submitDecision(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const submitter = (event.nativeEvent as SubmitEvent)
      .submitter as HTMLButtonElement | null;
    const decision = submitter?.value as ReviewDecisionStatus | undefined;
    if (!decision || !reviewerId.trim() || !comment.trim()) return;

    setSubmitting(true);
    setDecisionError(null);
    try {
      const decided = await api.decideReview(review.id, {
        status: decision,
        reviewer_id: reviewerId.trim(),
        comment: comment.trim(),
      });
      onDecision(decided);
    } catch (error: unknown) {
      setDecisionError(errorMessage(error));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="review-record">
      <div className="review-record-header">
        <div>
          <span className={`outcome-badge ${review.status}`}>
            {review.status === "approved" ? <CheckIcon /> : <ShieldIcon />}
            {statusLabels[review.status]}
          </span>
          <h2>Review {shortId(review.id)}</h2>
          <p>Workflow {shortId(review.workflow_id)}</p>
        </div>
        <span className="record-date">Created {formatDate(review.created_at)}</span>
      </div>

      <div className="routing-reason">
        <ShieldIcon />
        <div>
          <span className="section-kicker">Routing reason</span>
          <p>{review.reason}</p>
        </div>
      </div>

      <section className="candidate-section">
        <span className="section-kicker">Unreleased candidate</span>
        <p className="candidate-answer">{review.candidate_answer.answer}</p>
        <div className="citation-list">
          {review.candidate_answer.citations.map((citation, index) => (
            <span key={citation.chunk_id} title={citation.chunk_id}>
              [{index + 1}] {shortId(citation.chunk_id)}
            </span>
          ))}
        </div>
      </section>

      <section className="evidence-section">
        <div className="section-title-row">
          <div>
            <span className="section-kicker">Evidence snapshot</span>
            <h3>{review.evidence.length} retrieved chunks</h3>
          </div>
          <small>Captured when the answer was generated</small>
        </div>
        <div className="evidence-list">
          {review.evidence.map((evidence, index) => (
            <article
              key={evidence.chunk_id}
              className={citedChunkIds.has(evidence.chunk_id) ? "cited" : ""}
            >
              <div className="evidence-meta">
                <span>
                  <QuoteIcon /> Evidence {index + 1}
                </span>
                {citedChunkIds.has(evidence.chunk_id) && (
                  <span className="cited-label">
                    <CheckIcon /> Cited
                  </span>
                )}
              </div>
              <p>{evidence.content}</p>
              <footer>
                Chunk {shortId(evidence.chunk_id)} · Document {shortId(evidence.document_id)}
              </footer>
            </article>
          ))}
        </div>
      </section>

      {review.status === "pending" ? (
        <form className="decision-form" onSubmit={submitDecision}>
          <div className="section-title-row">
            <div>
              <span className="section-kicker">Accountable decision</span>
              <h3>Record your assessment</h3>
            </div>
            <small>Reviewer identity and rationale are required</small>
          </div>

          <div className="decision-fields">
            <div>
              <label className="field-label" htmlFor={`reviewer-${review.id}`}>
                Reviewer ID
              </label>
              <input
                id={`reviewer-${review.id}`}
                type="text"
                value={reviewerId}
                onChange={(event) => setReviewerId(event.target.value)}
                placeholder="e.g. analyst-042"
                maxLength={255}
                required
              />
            </div>
            <div>
              <label className="field-label" htmlFor={`rationale-${review.id}`}>
                Rationale
              </label>
              <textarea
                id={`rationale-${review.id}`}
                value={comment}
                onChange={(event) => setComment(event.target.value)}
                placeholder="Explain why the evidence does or does not support release…"
                rows={4}
                maxLength={4000}
                required
              />
            </div>
          </div>

          {decisionError && (
            <div className="inline-alert error" role="alert">
              {decisionError}
            </div>
          )}

          <div className="decision-actions">
            <button
              type="submit"
              className="danger-button"
              name="status"
              value="rejected"
              disabled={submitting || !reviewerId.trim() || !comment.trim()}
            >
              <CloseIcon /> {submitting ? "Saving decision…" : "Reject answer"}
            </button>
            <button
              type="submit"
              className="approve-button"
              name="status"
              value="approved"
              disabled={submitting || !reviewerId.trim() || !comment.trim()}
            >
              <CheckIcon /> {submitting ? "Saving decision…" : "Approve answer"}
            </button>
          </div>
        </form>
      ) : (
        <section className={`recorded-decision ${review.status}`}>
          {review.status === "approved" ? <CheckIcon /> : <CloseIcon />}
          <div>
            <span className="section-kicker">Recorded decision</span>
            <h3>{statusLabels[review.status]}</h3>
            <p>{review.reviewer_comment}</p>
            <small>
              {review.reviewer_id} · {review.decided_at ? formatDate(review.decided_at) : "Time unavailable"}
            </small>
          </div>
        </section>
      )}
    </div>
  );
}
