import { useEffect, useState } from "react";

import { api } from "./api";
import { ReviewIcon, ShieldIcon, SparkIcon } from "./components/Icons";
import { AnswerWorkbench } from "./views/AnswerWorkbench";
import { ReviewConsole } from "./views/ReviewConsole";

type View = "workbench" | "reviews";

function initialView(): View {
  return window.location.hash === "#reviews" ? "reviews" : "workbench";
}

export default function App() {
  const [view, setView] = useState<View>(initialView);
  const [requestedReviewId, setRequestedReviewId] = useState<string | null>(null);
  const [serviceStatus, setServiceStatus] = useState<
    "checking" | "healthy" | "unavailable"
  >("checking");
  const [version, setVersion] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    api
      .health()
      .then((health) => {
        if (active) {
          setServiceStatus("healthy");
          setVersion(health.version);
        }
      })
      .catch(() => {
        if (active) {
          setServiceStatus("unavailable");
        }
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const handleHashChange = () => setView(initialView());
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  function navigate(nextView: View) {
    window.location.hash = nextView === "reviews" ? "reviews" : "workbench";
    setView(nextView);
  }

  function openReview(reviewId: string) {
    setRequestedReviewId(reviewId);
    navigate("reviews");
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <button
          className="brand"
          type="button"
          onClick={() => navigate("workbench")}
          aria-label="Open answer workbench"
        >
          <span className="brand-mark">
            <ShieldIcon />
          </span>
          <span>
            <strong>Enterprise GenAI Lab</strong>
            <small>Governed intelligence</small>
          </span>
        </button>

        <nav className="primary-nav" aria-label="Primary navigation">
          <button
            type="button"
            className={view === "workbench" ? "nav-item active" : "nav-item"}
            onClick={() => navigate("workbench")}
            aria-current={view === "workbench" ? "page" : undefined}
          >
            <SparkIcon />
            Answer workbench
          </button>
          <button
            type="button"
            className={view === "reviews" ? "nav-item active" : "nav-item"}
            onClick={() => navigate("reviews")}
            aria-current={view === "reviews" ? "page" : undefined}
          >
            <ReviewIcon />
            Review console
          </button>
        </nav>

        <div className={`service-status ${serviceStatus}`} role="status">
          <span className="status-dot" />
          <span>
            {serviceStatus === "healthy"
              ? `API connected${version ? ` · v${version}` : ""}`
              : serviceStatus === "checking"
                ? "Checking API"
                : "API unavailable"}
          </span>
        </div>
      </header>

      <main>
        {view === "workbench" ? (
          <AnswerWorkbench onOpenReview={openReview} />
        ) : (
          <ReviewConsole requestedReviewId={requestedReviewId} />
        )}
      </main>

      <footer className="app-footer">
        <span>Evidence-first answers</span>
        <span aria-hidden="true">·</span>
        <span>Deterministic governance</span>
        <span aria-hidden="true">·</span>
        <span>Human accountability</span>
      </footer>
    </div>
  );
}
