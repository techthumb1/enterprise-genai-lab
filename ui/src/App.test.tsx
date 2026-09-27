import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

import App from "./App";

beforeEach(() => {
  window.location.hash = "";
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const path = String(input);
      if (path === "/health") {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              status: "healthy",
              service: "Enterprise GenAI Lab",
              version: "0.1.0",
              environment: "test",
            }),
            { status: 200, headers: { "Content-Type": "application/json" } },
          ),
        );
      }
      return Promise.resolve(
        new Response(JSON.stringify([]), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }),
  );
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("moves between the governed answer and review surfaces", async () => {
  render(<App />);

  expect(
    screen.getByRole("heading", { name: "Answer workbench" }),
  ).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /review console/i }));

  expect(
    await screen.findByRole("heading", { name: "Review console" }),
  ).toBeInTheDocument();
  expect(screen.getByText("No pending reviews")).toBeInTheDocument();
});
