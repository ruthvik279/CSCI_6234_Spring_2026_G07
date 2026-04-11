import { useEffect, useState } from "react";
import {
  analyzePullRequest,
  createRepository,
  fetchAnalysisHistory,
  fetchDashboard,
  fetchReport,
  fetchRules,
  getReportDownloadUrl,
  listPullRequests,
  listRepositories,
  updateRules,
} from "./api";

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
  const [knownRepositories, setKnownRepositories] = useState([]);
  const [pullRequests, setPullRequests] = useState([]);
  const [rules, setRules] = useState([]);
  const [report, setReport] = useState(null);
  const [history, setHistory] = useState([]);
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

  useEffect(() => {
    listRepositories()
      .then((data) => {
        setKnownRepositories(data.repositories);
        if (data.repositories.length && !activeRepository) {
          setActiveRepository(data.repositories[0]);
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!activeRepository?.repository_id) {
      return;
    }
    loadRepositoryWorkspace(activeRepository.repository_id);
  }, [activeRepository?.repository_id]);

  function updateRepositoryField(event) {
    const { name, value } = event.target;
    setRepositoryForm((current) => ({ ...current, [name]: value }));
  }

  function updateRule(index, field, value) {
    setRules((current) =>
      current.map((rule, ruleIndex) =>
        ruleIndex === index ? { ...rule, [field]: value } : rule
      )
    );
  }

  async function loadRepositoryWorkspace(repositoryId) {
    try {
      const [rulesData, reportData, historyData, pullRequestData] = await Promise.all([
        fetchRules(repositoryId),
        fetchReport(repositoryId),
        fetchAnalysisHistory(repositoryId),
        listPullRequests(repositoryId).catch(() => ({ pull_requests: [] })),
      ]);
      setRules(rulesData.rules);
      setReport(reportData);
      setHistory(historyData.history);
      setPullRequests(pullRequestData.pull_requests);
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function handleRepositorySubmit(event) {
    event.preventDefault();
    setBusyAction("repository");
    setMessage("");

    try {
      const repository = await createRepository(repositoryForm);
      setActiveRepository(repository);
      const repositoriesData = await listRepositories();
      setKnownRepositories(repositoriesData.repositories);
      await loadRepositoryWorkspace(repository.repository_id);
      setMessage(
        `Connected ${repository.owner}/${repository.repo_name}. Repository workspace is ready.`
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
      await loadRepositoryWorkspace(activeRepository.repository_id);
      setMessage(`Analyzed GitHub pull request #${pullRequestNumber}.`);
      await refreshDashboard();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusyAction("");
    }
  }

  async function handleRulesSave(event) {
    event.preventDefault();
    if (!activeRepository?.repository_id) {
      setMessage("Connect a GitHub repository first.");
      return;
    }

    setBusyAction("save-rules");
    setMessage("");
    try {
      const result = await updateRules({
        repository_id: activeRepository.repository_id,
        rules: rules.map((rule) => ({
          name: rule.name,
          severity: rule.severity,
          is_enabled: rule.is_enabled,
          threshold: rule.threshold === "" || rule.threshold === null ? null : Number(rule.threshold),
        })),
      });
      setRules(result.rules);
      setMessage("Rules updated successfully.");
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusyAction("");
    }
  }

  async function handleReportRefresh() {
    if (!activeRepository?.repository_id) {
      setMessage("Connect a GitHub repository first.");
      return;
    }
    setBusyAction("refresh-report");
    setMessage("");
    try {
      const reportData = await fetchReport(activeRepository.repository_id);
      setReport(reportData);
      const historyData = await fetchAnalysisHistory(activeRepository.repository_id);
      setHistory(historyData.history);
      setMessage("Report refreshed.");
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
            <span className="badge">
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
              <p className="eyebrow">Repositories</p>
              <h2>Connected Repository History</h2>
            </div>
            <span className="badge subtle">{knownRepositories.length} tracked</span>
          </div>

          {knownRepositories.length ? (
            <div className="results-stack">
              {knownRepositories.map((repository) => (
                <button
                  type="button"
                  className={`repo-card ${
                    activeRepository?.repository_id === repository.repository_id ? "repo-card-active" : ""
                  }`}
                  key={repository.repository_id}
                  onClick={() => setActiveRepository(repository)}
                >
                  <strong>{repository.name}</strong>
                  <span className="muted">
                    {repository.owner}/{repository.repo_name}
                  </span>
                </button>
              ))}
            </div>
          ) : (
            <div className="result-box empty-state">
              <p>No repositories have been connected yet.</p>
            </div>
          )}
        </article>

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

      <section className="workspace">
        <article className="panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Use Case</p>
              <h2>Configure Rules</h2>
            </div>
          </div>

          {activeRepository ? (
            <form className="form" onSubmit={handleRulesSave}>
              {rules.map((rule, index) => (
                <div className="rule-row" key={rule.rule_id || `${rule.name}-${index}`}>
                  <div className="rule-row-header">
                    <strong>{rule.name}</strong>
                    <label className="toggle">
                      <input
                        type="checkbox"
                        checked={rule.is_enabled}
                        onChange={(event) => updateRule(index, "is_enabled", event.target.checked)}
                      />
                      Enabled
                    </label>
                  </div>
                  <div className="inline-grid">
                    <label>
                      Severity
                      <select
                        value={rule.severity}
                        onChange={(event) => updateRule(index, "severity", event.target.value)}
                      >
                        <option value="low">low</option>
                        <option value="medium">medium</option>
                        <option value="high">high</option>
                      </select>
                    </label>
                    <label>
                      Threshold
                      <input
                        type="number"
                        value={rule.threshold ?? ""}
                        onChange={(event) => updateRule(index, "threshold", event.target.value)}
                      />
                    </label>
                  </div>
                </div>
              ))}
              <button type="submit" disabled={busyAction === "save-rules"}>
                {busyAction === "save-rules" ? "Saving..." : "Save Rules"}
              </button>
            </form>
          ) : (
            <div className="result-box empty-state">
              <p>Connect a repository to configure its rules.</p>
            </div>
          )}
        </article>

        <article className="panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Use Case</p>
              <h2>Generate Report</h2>
            </div>
            <div className="button-row">
              <button
                type="button"
                className="secondary-button"
                onClick={handleReportRefresh}
                disabled={!activeRepository || busyAction === "refresh-report"}
              >
                {busyAction === "refresh-report" ? "Refreshing..." : "Refresh Report"}
              </button>
              {activeRepository ? (
                <a
                  className="secondary-button link-button"
                  href={getReportDownloadUrl(activeRepository.repository_id)}
                  target="_blank"
                  rel="noreferrer"
                >
                  Download CSV
                </a>
              ) : null}
            </div>
          </div>

          {report ? (
            <div className="results-stack">
              <div className="result-box">
                <h3>Repository Summary</h3>
                <p>Pull requests analyzed: {report.pull_request_count}</p>
                <p>Total issues found: {report.total_issue_count}</p>
                <p>Average quality score: {report.average_quality_score}</p>
              </div>
              <div className="result-box">
                <h3>Issues By Severity</h3>
                <p className="muted">
                  {Object.keys(report.issues_by_severity).length
                    ? Object.entries(report.issues_by_severity)
                        .map(([severity, count]) => `${severity} ${count}`)
                        .join(", ")
                    : "No issues recorded yet."}
                </p>
              </div>
            </div>
          ) : (
            <div className="result-box empty-state">
              <p>No report data is available for the selected repository yet.</p>
            </div>
          )}
        </article>
      </section>

      <section className="workspace">
        <article className="panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">History</p>
              <h2>Analyzed Pull Request History</h2>
            </div>
            <span className="badge subtle">{history.length} analyzed</span>
          </div>

          {history.length ? (
            <div className="results-stack">
              {history.map((entry) => (
                <article className="comment-card" key={entry.pull_request_id}>
                  <p className="comment-path">PR #{entry.number}</p>
                  <h3>{entry.title}</h3>
                  <p className="muted">
                    status: {entry.status} | issues: {entry.issue_count} | comments: {entry.comment_count}
                  </p>
                  <p className="muted">
                    quality score: {entry.quality_score} | avg complexity: {entry.avg_complexity}
                  </p>
                </article>
              ))}
            </div>
          ) : (
            <div className="result-box empty-state">
              <p>No analyzed pull requests recorded yet.</p>
            </div>
          )}
        </article>
      </section>
    </main>
  );
}
