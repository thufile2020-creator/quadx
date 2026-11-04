// Member 1: copy into frontend/script.js and adapt to the actual UI.
// Run the frontend via Live Server (http://127.0.0.1:5500), not file://.
const API_BASE = "http://127.0.0.1:5000/api";
let accessToken = null;

async function api(path, options = {}) {
  const response = await fetch(API_BASE + path, {
    method: options.method || "GET",
    headers: {
      "Content-Type": "application/json",
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    },
    ...(options.body ? { body: JSON.stringify(options.body) } : {}),
  });
  const result = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(result.error || `HTTP ${response.status}`);
  return result;
}

async function login(email, password) {
  const result = await api("/auth/login", {
    method: "POST", body: { email, password },
  });
  accessToken = result.access_token; // In-memory for MVP; refresh after reload.
  return result.user;
}

async function previewEmissions(electricityKwh, dieselLitres) {
  return api("/calculate", {
    method: "POST", body: { electricity_kwh: electricityKwh, diesel_litres: dieselLitres },
  });
}

async function saveElectricityRecord(businessId, period, kwh) {
  return api(`/businesses/${businessId}/activities`, {
    method: "POST", body: { period, activity_type: "electricity", quantity: kwh },
  });
}

async function getMonthlySummary(businessId, period) {
  return api(`/businesses/${businessId}/summary?period=${encodeURIComponent(period)}`);
}

// Example only: call these functions from your existing buttons/forms.
// previewEmissions(500, 30).then(result => console.log(result.total_kg_co2e));
