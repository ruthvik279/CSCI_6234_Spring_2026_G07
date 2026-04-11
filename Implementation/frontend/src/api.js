const API_BASE = "http://127.0.0.1:8000";

export async function fetchDashboard() {
  const response = await fetch(`${API_BASE}/dashboard`);
  if (!response.ok) {
    throw new Error("Unable to load dashboard data.");
  }
  return response.json();
}

async function postJson(path, payload) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await extractError(response, path));
  }

  return response.json();
}

async function getJson(path) {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(await extractError(response, path));
  }
  return response.json();
}

async function extractError(response, path) {
  try {
    const payload = await response.json();
    return payload.detail || `Request to ${path} failed.`;
  } catch {
    const message = await response.text();
    return message || `Request to ${path} failed.`;
  }
}

export function createRepository(payload) {
  return postJson("/repositories", payload);
}

export function listRepositories() {
  return getJson("/repositories");
}

export function listPullRequests(repositoryId) {
  return getJson(`/repositories/${repositoryId}/pull-requests`);
}

export function analyzePullRequest(repositoryId, pullRequestNumber) {
  return postJson(`/repositories/${repositoryId}/pull-requests/${pullRequestNumber}/analyze`, {});
}

export function fetchRules(repositoryId) {
  return getJson(`/repositories/${repositoryId}/rules`);
}

export function updateRules(payload) {
  return postJson("/rules", payload);
}

export function fetchReport(repositoryId) {
  return getJson(`/reports/${repositoryId}`);
}

export function fetchAnalysisHistory(repositoryId) {
  return getJson(`/repositories/${repositoryId}/history`);
}

export function getReportDownloadUrl(repositoryId) {
  return `${API_BASE}/reports/${repositoryId}/download`;
}
