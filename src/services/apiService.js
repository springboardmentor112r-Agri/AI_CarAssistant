/**
 * Backend API helper — wraps fetch with auth token.
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

function getToken() {
  return localStorage.getItem('sla_token') || '';
}

function authHeaders() {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${getToken()}`,
  };
}

// ─── Contracts ───────────────────────────────────────────────────

export async function createContract(data) {
  const res = await fetch(`${API_URL}/api/contracts`, {
    method: 'POST', headers: authHeaders(), body: JSON.stringify(data),
  });
  const json = await res.json();
  if (res.status === 409) {
    const err = new Error(json.message || 'Contract already uploaded');
    err.code = 'DUPLICATE';
    err.contractId = json.contractId;
    throw err;
  }
  if (!res.ok) throw new Error(json.error || 'Failed to create contract');
  return json;
}

export async function checkContractExists(fileName) {
  const res = await fetch(`${API_URL}/api/contracts/check?file_name=${encodeURIComponent(fileName)}`, { headers: authHeaders() });
  return res.json();
}

export async function cleanupDuplicateContracts() {
  const res = await fetch(`${API_URL}/api/contracts/cleanup-duplicates`, {
    method: 'POST', headers: authHeaders(),
  });
  return res.json();
}

export async function getContracts() {
  const res = await fetch(`${API_URL}/api/contracts`, { headers: authHeaders() });
  return res.json();
}

export async function deleteContract(id) {
  const res = await fetch(`${API_URL}/api/contracts/${id}`, {
    method: 'DELETE', headers: authHeaders(),
  });
  return res.json();
}

// ─── SLA ─────────────────────────────────────────────────────────

export async function createSLA(data) {
  const res = await fetch(`${API_URL}/api/sla`, {
    method: 'POST', headers: authHeaders(), body: JSON.stringify(data),
  });
  return res.json();
}

export async function getSLAs() {
  const res = await fetch(`${API_URL}/api/sla`, { headers: authHeaders() });
  return res.json();
}

export async function getSLAsWithContracts() {
  const res = await fetch(`${API_URL}/api/sla/with-contracts`, { headers: authHeaders() });
  return res.json();
}

export async function getSLAByContract(contractId) {
  const res = await fetch(`${API_URL}/api/sla/contract/${contractId}`, { headers: authHeaders() });
  return res.json();
}

export async function deleteSLA(id) {
  const res = await fetch(`${API_URL}/api/sla/${id}`, {
    method: 'DELETE', headers: authHeaders(),
  });
  return res.json();
}

// ─── Vehicles ────────────────────────────────────────────────────

export async function upsertVehicle(data) {
  const res = await fetch(`${API_URL}/api/vehicles`, {
    method: 'POST', headers: authHeaders(), body: JSON.stringify(data),
  });
  return res.json();
}

export async function getVehicleByVIN(vin) {
  const res = await fetch(`${API_URL}/api/vehicles/vin/${encodeURIComponent(vin)}`, { headers: authHeaders() });
  return res.json();
}

// ─── Prices ──────────────────────────────────────────────────────

export async function createPrice(data) {
  const res = await fetch(`${API_URL}/api/prices`, {
    method: 'POST', headers: authHeaders(), body: JSON.stringify(data),
  });
  return res.json();
}

export async function getPricesByVehicle(vehicleId) {
  const res = await fetch(`${API_URL}/api/prices/vehicle/${vehicleId}`, { headers: authHeaders() });
  return res.json();
}

export async function getMarketPrices(make, model, year) {
  const res = await fetch(
    `${API_URL}/api/prices/market/${encodeURIComponent(make)}/${encodeURIComponent(model)}/${encodeURIComponent(year)}`,
    { headers: authHeaders() }
  );
  if (!res.ok) throw new Error('Failed to fetch market prices');
  return res.json();
}

// ─── Dealers ─────────────────────────────────────────────────────

export async function createDealer(data) {
  const res = await fetch(`${API_URL}/api/dealers`, {
    method: 'POST', headers: authHeaders(), body: JSON.stringify(data),
  });
  return res.json();
}

export async function getDealers() {
  const res = await fetch(`${API_URL}/api/dealers`, { headers: authHeaders() });
  return res.json();
}

// ─── Negotiations ────────────────────────────────────────────────

export async function createThread(data) {
  const res = await fetch(`${API_URL}/api/negotiations/threads`, {
    method: 'POST', headers: authHeaders(), body: JSON.stringify(data),
  });
  return res.json();
}

export async function getThreadsByContract(contractId) {
  const res = await fetch(`${API_URL}/api/negotiations/threads/contract/${contractId}`, { headers: authHeaders() });
  return res.json();
}

export async function addMessage(data) {
  const res = await fetch(`${API_URL}/api/negotiations/messages`, {
    method: 'POST', headers: authHeaders(), body: JSON.stringify(data),
  });
  return res.json();
}

export async function getMessages(threadId) {
  const res = await fetch(`${API_URL}/api/negotiations/messages/${threadId}`, { headers: authHeaders() });
  return res.json();
}

// ─── Alerts ──────────────────────────────────────────────────────

export async function createAlert(data) {
  const res = await fetch(`${API_URL}/api/alerts`, {
    method: 'POST', headers: authHeaders(), body: JSON.stringify(data),
  });
  return res.json();
}

export async function getAlerts() {
  const res = await fetch(`${API_URL}/api/alerts`, { headers: authHeaders() });
  return res.json();
}

export async function getAlertsByContract(contractId) {
  const res = await fetch(`${API_URL}/api/alerts/contract/${contractId}`, { headers: authHeaders() });
  return res.json();
}

// ─── Comparisons ─────────────────────────────────────────────────

export async function createComparison(data) {
  const res = await fetch(`${API_URL}/api/comparisons`, {
    method: 'POST', headers: authHeaders(), body: JSON.stringify(data),
  });
  return res.json();
}

export async function getComparisons() {
  const res = await fetch(`${API_URL}/api/comparisons`, { headers: authHeaders() });
  return res.json();
}
