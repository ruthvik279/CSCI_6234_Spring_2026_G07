const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

function withDays(path, days) {
  return days ? `${path}?days=${days}` : path;
}

export async function fetchDashboard(days = null) {
  const response = await fetch(`${API_BASE}${withDays("/dashboard", days)}`);
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

export function fetchReport(repositoryId, days = null) {
  return getJson(withDays(`/reports/${repositoryId}`, days));
}

export function fetchAnalysisHistory(repositoryId, days = null) {
  return getJson(withDays(`/repositories/${repositoryId}/history`, days));
}

export function getReportDownloadUrl(repositoryId, days = null) {
  return `${API_BASE}${withDays(`/reports/${repositoryId}/download`, days)}`;
}
