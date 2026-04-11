import { useEffect, useState } from "react";
import { analyzePullRequest, createRepository, fetchDashboard, listPullRequests } from "./api";

const fallbackMetrics = {
  repository_count: 0,
  pull_request_count: 0,
  total_issue_count: 0,
  average_quality_score: 0,
};

const initialRepositoryForm = {
  name: "Demo Repo",
  github_url: "https://github.com/example/demo-repo",
  access_token: "demo-token",
};

export default function App() {
  const [metrics, setMetrics] = useState(fallbackMetrics);
  const [status, setStatus] = useState("loading");
  const [repositoryForm, setRepositoryForm] = useState(initialRepositoryForm);
  const [activeRepository, setActiveRepository] = useState(null);
  const [pullRequests, setPullRequests] = useState([]);
  const [lastRun, setLastRun] = useState(null);
  const [message, setMessage] = useState("");
  const [busyAction, setBusyAction] = useState("");

  async function refreshDashboard() {
    const data = await fetchDashboard();
    setMetrics(data);
    setStatus("ready");
  }

  useEffect(() => {
    let active = true;

    refreshDashboard()
      .then((data) => {
        if (!active) {
          return;
        }
        return data;
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

  function updateRepositoryField(event) {
    const { name, value } = event.target;
    setRepositoryForm((current) => ({ ...current, [name]: value }));
  }

  async function handleRepositorySubmit(event) {
    event.preventDefault();
    setBusyAction("repository");
    setMessage("");

    try {
      const repository = await createRepository(repositoryForm);
      setActiveRepository(repository);
      const pullRequestData = await listPullRequests(repository.repository_id);
      setPullRequests(pullRequestData.pull_requests);
      setMessage(
        `Connected ${repository.owner}/${repository.repo_name}. Loaded ${pullRequestData.pull_requests.length} open pull requests.`
      );
      await refreshDashboard();
    } catch (error) {
      setStatus("offline");
      setMessage(error.message);
    } finally {
      setBusyAction("");
    }
  }

  async function handlePullRequestRefresh() {
    if (!activeRepository?.repository_id) {
      setMessage("Connect a GitHub repository first.");
      return;
    }

    setBusyAction("refresh-pull-requests");
    setMessage("");
    try {
      const pullRequestData = await listPullRequests(activeRepository.repository_id);
      setPullRequests(pullRequestData.pull_requests);
      setMessage(`Loaded ${pullRequestData.pull_requests.length} open pull requests from GitHub.`);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusyAction("");
    }
  }

  async function handleAnalyzeGitHubPullRequest(pullRequestNumber) {
    if (!activeRepository?.repository_id) {
      setMessage("Connect a GitHub repository first.");
      return;
    }

    setBusyAction(`analyze-${pullRequestNumber}`);
    setMessage("");
    try {
      const result = await analyzePullRequest(activeRepository.repository_id, pullRequestNumber);
      setLastRun(result);
      setMessage(`Analyzed GitHub pull request #${pullRequestNumber}.`);
      await refreshDashboard();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusyAction("");
    }
  }

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
        {message ? <p className="feedback">{message}</p> : null}
      </section>

      <section className="workspace">
        <article className="panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Step 1</p>
              <h2>Connect Repository</h2>
            </div>
            <span className="badge">
              {activeRepository ? "Connected" : "Waiting"}
            </span>
          </div>

          <form className="form" onSubmit={handleRepositorySubmit}>
            <label>
              Repository Name
              <input
                name="name"
                value={repositoryForm.name}
                onChange={updateRepositoryField}
                required
              />
            </label>
            <label>
              GitHub URL
              <input
                name="github_url"
                value={repositoryForm.github_url}
                onChange={updateRepositoryField}
                required
              />
            </label>
            <label>
              Access Token
              <input
                name="access_token"
                value={repositoryForm.access_token}
                onChange={updateRepositoryField}
                required
              />
            </label>
            <button type="submit" disabled={busyAction === "repository"}>
              {busyAction === "repository" ? "Connecting..." : "Connect Repository"}
            </button>
          </form>

          {activeRepository ? (
            <div className="result-box">
              <h3>Active Repository</h3>
              <p>{activeRepository.name}</p>
              <p className="muted">{activeRepository.github_url}</p>
              <p className="muted">
                Repository ID: {activeRepository.repository_id}
              </p>
            </div>
          ) : null}
        </article>

        <article className="panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Step 2</p>
              <h2>Analyze Real GitHub Pull Requests</h2>
            </div>
            <span className="badge subtle">
              {lastRun ? `${lastRun.issues_found} issues found` : "No run yet"}
            </span>
          </div>

          <div className="action-row">
            <button
              type="button"
              className="secondary-button"
              onClick={handlePullRequestRefresh}
              disabled={busyAction === "refresh-pull-requests"}
            >
              {busyAction === "refresh-pull-requests" ? "Refreshing..." : "Refresh Open PRs"}
            </button>
          </div>

          {pullRequests.length ? (
            <div className="results-stack">
              {pullRequests.map((pullRequest) => (
                <article className="comment-card" key={pullRequest.number}>
                  <p className="comment-path">PR #{pullRequest.number}</p>
                  <h3>{pullRequest.title}</h3>
                  <p className="muted">
                    {pullRequest.author} • {pullRequest.state}
                  </p>
                  <p>
                    <a href={pullRequest.html_url} target="_blank" rel="noreferrer">
                      View on GitHub
                    </a>
                  </p>
                  <button
                    type="button"
                    onClick={() => handleAnalyzeGitHubPullRequest(pullRequest.number)}
                    disabled={busyAction === `analyze-${pullRequest.number}`}
                  >
                    {busyAction === `analyze-${pullRequest.number}`
                      ? "Analyzing..."
                      : "Analyze This PR"}
                  </button>
                </article>
              ))}
            </div>
          ) : (
            <div className="result-box empty-state">
              <p>No open GitHub pull requests loaded yet.</p>
            </div>
          )}
        </article>

      </section>

      <section className="workspace">
        <article className="panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Results</p>
              <h2>Latest Review Output</h2>
            </div>
          </div>

          {lastRun ? (
            <div className="results-stack">
              <div className="result-box">
                <h3>Summary</h3>
                <p>Issues found: {lastRun.issues_found}</p>
                <p className="muted">
                  Severity mix: {Object.entries(lastRun.issues_by_severity)
                    .map(([severity, count]) => `${severity} ${count}`)
                    .join(", ")}
                </p>
                <p className="muted">
                  Quality score: {lastRun.metrics.code_quality_score}
                </p>
              </div>

              <div className="comment-list">
                {lastRun.comments.map((comment) => (
                  <article className="comment-card" key={comment.comment_id}>
                    <p className="comment-path">
                      {comment.file_path}:{comment.line_number}
                    </p>
                    <p>{comment.body}</p>
                  </article>
                ))}
              </div>
            </div>
          ) : (
            <div className="result-box empty-state">
              <p>No pull request analysis has been run from the UI yet.</p>
            </div>
          )}
        </article>
      </section>
    </main>
  );
}
