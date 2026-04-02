const BASE = '/api'

function getToken() {
  return localStorage.getItem('autoguard_token')
}

function headers(isForm = false) {
  const h = { Authorization: `Bearer ${getToken()}` }
  if (!isForm) h['Content-Type'] = 'application/json'
  return h
}

async function req(path, opts = {}) {
  const res = await fetch(BASE + path, opts)
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.detail || 'Request failed')
  return data
}

// ── Auth ──────────────────────────────────────────────────
export const authAPI = {
  register: (body) => req('/auth/register', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  login:    (body) => req('/auth/login',    { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
}

// ── Contracts ─────────────────────────────────────────────
export const contractAPI = {
  upload: (file) => {
    const fd = new FormData()
    fd.append('file', file)
    return req('/contracts/upload', { method: 'POST', headers: headers(true), body: fd })
  },
  list:   ()   => req('/contracts/',        { headers: headers() }),
  get:    (id) => req(`/contracts/${id}`,   { headers: headers() }),
  delete: (id) => req(`/contracts/${id}`,   { method: 'DELETE', headers: headers() }),
}

// ── Extraction ────────────────────────────────────────────
export const extractionAPI = {
  analyze:    (id) => req(`/extraction/${id}/analyze`, { method: 'POST', headers: headers() }),
  getResults: (id) => req(`/extraction/${id}/results`, { headers: headers() }),
}

// ── VIN ───────────────────────────────────────────────────
export const vinAPI = {
  lookup: (vin) => req(`/vin/${vin}`, { headers: headers() }),
}

// ── Chat ──────────────────────────────────────────────────
export const chatAPI = {
  send:       (contract_id, message) => req('/chat/', { method: 'POST', headers: headers(), body: JSON.stringify({ contract_id, message }) }),
  getHistory: (contract_id)          => req(`/chat/${contract_id}/history`, { headers: headers() }),
}
