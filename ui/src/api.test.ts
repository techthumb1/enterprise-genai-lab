import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, api } from "./api";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("api client", () => {
  it("submits governed answer requests without credential headers", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          workflow_id: "workflow-id",
          processing_run_id: "run-id",
          provider: "fake",
          model: "deterministic",
          retrieved_evidence_count: 1,
          final_answer: {
            answer: "Grounded answer.",
            citations: [],
            abstained: false,
            abstention_reason: null,
          },
          verification: { valid: true, errors: [] },
          risk: { disposition: "allow", reason: "grounding policy passed" },
          review_id: null,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await api.answer({
      query: "What does the evidence say?",
      processing_run_id: "run-id",
      risk_tier: "standard",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/answer",
      expect.objectContaining({
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
      }),
    );
    const options = fetchMock.mock.calls[0]?.[1] as RequestInit;
    expect(options.headers).not.toHaveProperty("Authorization");
  });

  it("surfaces API detail on failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "generation provider is not configured" }), {
          status: 503,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(
      api.answer({ query: "Question", processing_run_id: "run-id", risk_tier: "high" }),
    ).rejects.toEqual(
      new ApiError("generation provider is not configured", 503),
    );
  });
});
