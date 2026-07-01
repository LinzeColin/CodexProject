const API_BASE = "/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `HTTP ${response.status}`);
  }
  return response.json();
}

export function getDashboardSummary() {
  return request("/dashboard/summary");
}

export function listCases() {
  return request("/cases?limit=100");
}

export function createCase(payload) {
  return request("/cases", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function regenerateReport(caseId) {
  return request(`/reports/${caseId}`, { method: "POST" });
}

export function getModelSettings() {
  return request("/settings/models");
}

export function saveModelSettings(configs) {
  return request("/settings/models", {
    method: "PUT",
    body: JSON.stringify(configs)
  });
}

export function reportDownloadUrl(caseId) {
  return `${API_BASE}/reports/${caseId}/download`;
}

