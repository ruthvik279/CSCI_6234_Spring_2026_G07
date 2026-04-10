const API_BASE = "http://127.0.0.1:8000";

export async function fetchDashboard() {
  const response = await fetch(`${API_BASE}/dashboard`);
  if (!response.ok) {
    throw new Error("Unable to load dashboard data.");
  }
  return response.json();
}
