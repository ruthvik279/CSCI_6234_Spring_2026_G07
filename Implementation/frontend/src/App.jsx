import { useEffect, useState } from "react";
import { fetchDashboard } from "./api";

const fallbackMetrics = {
  repository_count: 0,
  pull_request_count: 0,
  total_issue_count: 0,
  average_quality_score: 0,
};

export default function App() {
  const [metrics, setMetrics] = useState(fallbackMetrics);
  const [status, setStatus] = useState("loading");

  useEffect(() => {
    let active = true;

    fetchDashboard()
      .then((data) => {
        if (!active) {
          return;
        }
        setMetrics(data);
        setStatus("ready");
      })
      .catch(() => {
        if (!active) {
          return;
        }
        setStatus("offline");
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <main className="app-shell">
      <section className="hero">
        <p className="eyebrow">Code Review Automation Assistant</p>
        <h1>Review pull requests faster with automated quality checks.</h1>
        <p className="lede">
          This starter dashboard reflects the UML use cases: connect repositories,
          configure rules, review findings, and generate reports.
        </p>
      </section>

      <section className="grid">
        <article className="card">
          <h2>Repositories</h2>
          <strong>{metrics.repository_count}</strong>
        </article>
        <article className="card">
          <h2>Pull Requests</h2>
          <strong>{metrics.pull_request_count}</strong>
        </article>
        <article className="card">
          <h2>Issues Found</h2>
          <strong>{metrics.total_issue_count}</strong>
        </article>
        <article className="card">
          <h2>Quality Score</h2>
          <strong>{metrics.average_quality_score}</strong>
        </article>
      </section>

      <section className="status-panel">
        <h2>System Status</h2>
        <p>
          {status === "ready"
            ? "Backend connection is active."
            : "Backend not running yet. Start the FastAPI server to populate live metrics."}
        </p>
      </section>
    </main>
  );
}
