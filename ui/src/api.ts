import type {
  AnswerResponse,
  HealthResponse,
  ProcessingRun,
  ReviewDecision,
  ReviewRecord,
  ReviewStatus,
  RiskTier,
} from "./types";

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...options,
    headers: {
      Accept: "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);
    const detail =
      typeof body === "object" && body !== null && "detail" in body
        ? String(body.detail)
        : `Request failed with status ${response.status}`;
    throw new ApiError(detail, response.status);
  }

  return (await response.json()) as T;
}

export const api = {
  health: (): Promise<HealthResponse> => request("/health"),

  processingRuns: (): Promise<ProcessingRun[]> =>
    request("/api/processing-runs?ready_only=true&limit=100"),

  answer: (input: {
    query: string;
    processing_run_id: string;
    risk_tier: RiskTier;
  }): Promise<AnswerResponse> =>
    request("/api/answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    }),

  reviews: (status: ReviewStatus, limit = 100): Promise<ReviewRecord[]> =>
    request(`/api/reviews?status=${status}&limit=${limit}`),

  decideReview: (
    reviewId: string,
    decision: ReviewDecision,
  ): Promise<ReviewRecord> =>
    request(`/api/reviews/${reviewId}/decision`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(decision),
    }),
};
