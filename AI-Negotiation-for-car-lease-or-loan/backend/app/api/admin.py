from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from app.api.deps import get_current_user
from app.models.models import User
from app.core.config import settings
from app.services.llm_logger import (
  get_overall_stats,
  get_daily_stats,
  get_module_stats,
  get_recent_logs,
  get_all_users_stats,
  get_documents_overview,
  get_document_status_counts,
  get_system_health,
  get_hourly_stats,
  get_fairness_score_distribution,
  get_recent_activity,
)

router = APIRouter()

def require_admin(current_user: User = Depends(get_current_user)):
  """
  Dependency that checks if current user is admin.
  Admin = user whose email matches ADMIN_EMAIL in .env
  """
  if not settings.ADMIN_EMAIL or current_user.email != settings.ADMIN_EMAIL:
    raise HTTPException(
      403,
      "Admin access required"
    )
  return current_user

# ─── API ENDPOINTS ──────────────────────────────────────

@router.get("/stats")
async def admin_stats(admin: User = Depends(require_admin)):
    return {
        "overall": await get_overall_stats(),
        "daily": await get_daily_stats(days=7),
        "modules": await get_module_stats(),
    }

@router.get("/logs")
async def admin_logs(limit: int = 20, admin: User = Depends(require_admin)):
    limit = min(max(1, limit), 100)
    return await get_recent_logs(limit)

@router.get("/users")
async def admin_users(admin: User = Depends(require_admin)):
    return await get_all_users_stats()

@router.get("/documents")
async def admin_documents(admin: User = Depends(require_admin)):
    return await get_documents_overview()

@router.get("/document-statuses")
async def admin_document_statuses(admin: User = Depends(require_admin)):
    return await get_document_status_counts()

@router.get("/health")
async def admin_health(admin: User = Depends(require_admin)):
    return await get_system_health()

@router.get("/hourly")
async def admin_hourly(
    hours: int = Query(default=24, ge=1, le=168),
    admin: User = Depends(require_admin),
):
    return await get_hourly_stats(hours)

@router.get("/fairness-distribution")
async def admin_fairness_distribution(admin: User = Depends(require_admin)):
    return await get_fairness_score_distribution()

@router.get("/activity")
async def admin_activity(
    limit: int = Query(default=30, ge=1, le=100),
    admin: User = Depends(require_admin),
):
    return await get_recent_activity(limit)


# ─── ADMIN DASHBOARD PAGE ────────────────────────────────

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(admin: User = Depends(require_admin)):
    return DASHBOARD_HTML


# ─── INLINE HTML TEMPLATE ────────────────────────────────

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Car Contract AI — Admin</title>
<style>
  :root {
    --bg: #0f1117;
    --surface: #1a1d27;
    --surface2: #232733;
    --border: #2d3140;
    --text: #e4e6eb;
    --text2: #9ca0ab;
    --accent: #6366f1;
    --accent2: #818cf8;
    --green: #22c55e;
    --red: #ef4444;
    --amber: #f59e0b;
    --cyan: #06b6d4;
    --pink: #ec4899;
    --radius: 12px;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
    min-height: 100vh;
  }

  /* ─ Layout ─ */
  .shell { max-width: 1440px; margin: 0 auto; padding: 24px; }
  header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 28px; flex-wrap: wrap; gap: 12px; }
  header h1 { font-size: 22px; font-weight: 700; }
  header h1 span { color: var(--accent2); }
  .header-right { display: flex; gap: 10px; align-items: center; }
  .badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;
    background: rgba(34,197,94,.12); color: var(--green);
  }
  .badge::before { content: ''; width: 7px; height: 7px; border-radius: 50%; background: var(--green); animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: .4; } }

  .btn-refresh {
    background: var(--surface2); border: 1px solid var(--border); color: var(--text2);
    padding: 6px 14px; border-radius: 8px; font-size: 13px; cursor: pointer;
    transition: all .15s;
  }
  .btn-refresh:hover { background: var(--accent); color: #fff; border-color: var(--accent); }
  .btn-refresh:disabled { opacity: .5; cursor: not-allowed; }

  /* ─ Tabs ─ */
  .tabs {
    display: flex; gap: 4px; margin-bottom: 24px;
    background: var(--surface); border-radius: 10px; padding: 4px;
    overflow-x: auto; -webkit-overflow-scrolling: touch;
  }
  .tab {
    padding: 8px 18px; border-radius: 8px; border: none; background: none;
    color: var(--text2); font-size: 13px; font-weight: 500; cursor: pointer;
    white-space: nowrap; transition: all .15s;
  }
  .tab:hover { color: var(--text); }
  .tab.active { background: var(--accent); color: #fff; }
  .page { display: none; }
  .page.active { display: block; }

  /* ─ Cards / Grid ─ */
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: 14px; margin-bottom: 24px;
  }
  .kpi {
    background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
    padding: 18px 20px; transition: border-color .15s;
  }
  .kpi:hover { border-color: var(--accent); }
  .kpi-label { font-size: 12px; color: var(--text2); text-transform: uppercase; letter-spacing: .5px; margin-bottom: 6px; }
  .kpi-value { font-size: 26px; font-weight: 700; }
  .kpi-sub { font-size: 12px; color: var(--text2); margin-top: 4px; }
  .kpi-value.green { color: var(--green); }
  .kpi-value.red { color: var(--red); }
  .kpi-value.amber { color: var(--amber); }
  .kpi-value.cyan { color: var(--cyan); }
  .kpi-value.pink { color: var(--pink); }
  .kpi-value.accent { color: var(--accent2); }

  .row { display: grid; gap: 18px; margin-bottom: 24px; }
  .row-2 { grid-template-columns: 1fr 1fr; }
  .row-3 { grid-template-columns: 1fr 1fr 1fr; }
  @media (max-width: 1024px) { .row-2, .row-3 { grid-template-columns: 1fr; } }

  .card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 20px; overflow: hidden;
  }
  .card-title { font-size: 14px; font-weight: 600; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
  .card-title .icon { font-size: 16px; }

  /* ─ Charts (inline SVG) ─ */
  .chart-container { width: 100%; overflow-x: auto; }
  svg.chart { display: block; }

  /* ─ Bar chart ─ */
  .bar-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
  .bar-label { width: 130px; font-size: 12px; color: var(--text2); text-align: right; flex-shrink: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .bar-track { flex: 1; height: 22px; background: var(--surface2); border-radius: 4px; overflow: hidden; position: relative; }
  .bar-fill { height: 100%; border-radius: 4px; transition: width .6s ease; min-width: 2px; }
  .bar-val { position: absolute; right: 8px; top: 50%; transform: translateY(-50%); font-size: 11px; font-weight: 600; color: var(--text); }

  /* ─ Tables ─ */
  .table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { text-align: left; padding: 10px 12px; border-bottom: 2px solid var(--border); color: var(--text2); font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: .5px; white-space: nowrap; }
  td { padding: 10px 12px; border-bottom: 1px solid var(--border); white-space: nowrap; }
  tr:hover td { background: rgba(99,102,241,.04); }
  .pill {
    display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 11px; font-weight: 600;
  }
  .pill-ready { background: rgba(34,197,94,.12); color: var(--green); }
  .pill-processing, .pill-pending, .pill-extraction_complete { background: rgba(245,158,11,.12); color: var(--amber); }
  .pill-error, .pill-sla_failed { background: rgba(239,68,68,.12); color: var(--red); }

  .status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
  .status-dot.ok { background: var(--green); }
  .status-dot.warn { background: var(--amber); }
  .status-dot.err { background: var(--red); }

  .activity-type {
    display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; text-transform: uppercase;
  }
  .activity-type.upload { background: rgba(99,102,241,.15); color: var(--accent2); }
  .activity-type.chat { background: rgba(6,182,212,.15); color: var(--cyan); }
  .activity-type.llm_error { background: rgba(239,68,68,.15); color: var(--red); }

  .mono { font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace; font-size: 12px; }
  .truncate { max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

  .empty { text-align: center; padding: 40px 20px; color: var(--text2); }

  /* ─ Loading / Error ─ */
  .loader { display: flex; align-items: center; justify-content: center; padding: 60px; }
  .spinner {
    width: 32px; height: 32px; border: 3px solid var(--border);
    border-top-color: var(--accent); border-radius: 50%;
    animation: spin .7s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .error-banner {
    background: rgba(239,68,68,.1); border: 1px solid rgba(239,68,68,.3);
    border-radius: 8px; padding: 12px 16px; margin-bottom: 16px;
    color: var(--red); font-size: 13px; display: none;
  }

  /* ─ Score colors ─ */
  .score-good { color: var(--green); }
  .score-ok { color: var(--amber); }
  .score-bad { color: var(--red); }

  /* auto-refresh indicator */
  .auto-refresh { font-size: 11px; color: var(--text2); }
</style>
</head>
<body>
<div class="shell">

<header>
  <h1><span>Car Contract AI</span> — Admin Dashboard</h1>
  <div class="header-right">
    <span class="auto-refresh" id="lastUpdated"></span>
    <button class="btn-refresh" id="btnRefresh" onclick="loadAll()">Refresh</button>
    <div class="badge">System Online</div>
  </div>
</header>

<div id="errorBanner" class="error-banner"></div>

<div class="tabs" role="tablist">
  <button class="tab active" data-page="overview">Overview</button>
  <button class="tab" data-page="llm">LLM Analytics</button>
  <button class="tab" data-page="users">Users</button>
  <button class="tab" data-page="documents">Documents</button>
  <button class="tab" data-page="activity">Activity Feed</button>
</div>

<!-- ═══════════════ OVERVIEW TAB ═══════════════ -->
<div id="page-overview" class="page active">
  <div class="kpi-grid" id="kpiGrid">
    <div class="loader"><div class="spinner"></div></div>
  </div>
  <div class="row row-2">
    <div class="card">
      <div class="card-title"><span class="icon">📊</span> Daily LLM Calls (7 days)</div>
      <div class="chart-container" id="dailyChart"></div>
    </div>
    <div class="card">
      <div class="card-title"><span class="icon">⚡</span> Calls by Module</div>
      <div id="moduleChart"></div>
    </div>
  </div>
  <div class="row row-2">
    <div class="card">
      <div class="card-title"><span class="icon">📄</span> Document Pipeline</div>
      <div id="statusChart"></div>
    </div>
    <div class="card">
      <div class="card-title"><span class="icon">⚖️</span> Fairness Score Distribution</div>
      <div id="fairnessChart"></div>
    </div>
  </div>
</div>

<!-- ═══════════════ LLM TAB ═══════════════ -->
<div id="page-llm" class="page">
  <div class="row row-2">
    <div class="card">
      <div class="card-title"><span class="icon">🕐</span> Hourly Calls (24h)</div>
      <div class="chart-container" id="hourlyChart"></div>
    </div>
    <div class="card">
      <div class="card-title"><span class="icon">🔑</span> Module Breakdown</div>
      <div id="moduleTable"></div>
    </div>
  </div>
  <div class="card">
    <div class="card-title"><span class="icon">📋</span> Recent LLM Calls</div>
    <div class="table-wrap" id="logsTable">
      <div class="loader"><div class="spinner"></div></div>
    </div>
  </div>
</div>

<!-- ═══════════════ USERS TAB ═══════════════ -->
<div id="page-users" class="page">
  <div class="card">
    <div class="card-title"><span class="icon">👤</span> All Users</div>
    <div class="table-wrap" id="usersTable">
      <div class="loader"><div class="spinner"></div></div>
    </div>
  </div>
</div>

<!-- ═══════════════ DOCUMENTS TAB ═══════════════ -->
<div id="page-documents" class="page">
  <div class="card">
    <div class="card-title"><span class="icon">📁</span> All Documents</div>
    <div class="table-wrap" id="docsTable">
      <div class="loader"><div class="spinner"></div></div>
    </div>
  </div>
</div>

<!-- ═══════════════ ACTIVITY TAB ═══════════════ -->
<div id="page-activity" class="page">
  <div class="card">
    <div class="card-title"><span class="icon">🔔</span> Recent Activity</div>
    <div class="table-wrap" id="activityTable">
      <div class="loader"><div class="spinner"></div></div>
    </div>
  </div>
</div>

</div><!-- .shell -->

<script>
/* ─── State ─────────────────────────────────────── */
let TOKEN = null;
const API = window.location.origin;

function getToken() {
  if (TOKEN) return TOKEN;
  const params = new URLSearchParams(window.location.search);
  TOKEN = params.get('token');
  if (!TOKEN) {
    const stored = localStorage.getItem('admin_token');
    if (stored) TOKEN = stored;
  }
  if (TOKEN) localStorage.setItem('admin_token', TOKEN);
  return TOKEN;
}

async function api(path) {
  const token = getToken();
  if (!token) throw new Error('No auth token. Append ?token=YOUR_JWT to the URL.');
  const r = await fetch(API + '/admin/' + path, {
    headers: { 'Authorization': 'Bearer ' + token },
  });
  if (r.status === 401 || r.status === 403) {
    localStorage.removeItem('admin_token');
    throw new Error('Auth failed (' + r.status + '). Check your token.');
  }
  if (!r.ok) throw new Error('API error: ' + r.status);
  return r.json();
}

function showError(msg) {
  const b = document.getElementById('errorBanner');
  b.textContent = msg;
  b.style.display = 'block';
  setTimeout(() => b.style.display = 'none', 8000);
}

/* ─── Tabs ──────────────────────────────────────── */
document.querySelectorAll('.tab').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('page-' + btn.dataset.page).classList.add('active');
  });
});

/* ─── Formatters ────────────────────────────────── */
function fmtNum(n) { return (n || 0).toLocaleString(); }
function fmtCost(n) { return '$' + (n || 0).toFixed(4); }
function fmtPct(n) { return (n || 0).toFixed(1) + '%'; }
function fmtMs(n) { return (n || 0).toLocaleString() + 'ms'; }
function fmtTime(iso) {
  if (!iso) return '-';
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) + ' ' +
         d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
}
function fmtDate(iso) {
  if (!iso) return '-';
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}
function scoreClass(s) {
  if (s == null) return '';
  if (s >= 70) return 'score-good';
  if (s >= 40) return 'score-ok';
  return 'score-bad';
}
function statusPill(s) {
  return '<span class="pill pill-' + s + '">' + s + '</span>';
}

/* ─── SVG Bar Chart ─────────────────────────────── */
function svgBarChart(data, labelKey, valueKey, color, width, height) {
  if (!data || data.length === 0) return '<div class="empty">No data</div>';
  const max = Math.max(...data.map(d => d[valueKey] || 0), 1);
  const barH = Math.min(28, Math.floor((height - 20) / data.length));
  const gap = 4;
  const labelW = 90;
  const realH = data.length * (barH + gap) + 10;

  let svg = '<svg class="chart" width="' + width + '" height="' + realH + '" viewBox="0 0 ' + width + ' ' + realH + '">';
  data.forEach((d, i) => {
    const y = i * (barH + gap) + 5;
    const val = d[valueKey] || 0;
    const bw = Math.max(2, ((val / max) * (width - labelW - 60)));
    // label
    svg += '<text x="' + (labelW - 6) + '" y="' + (y + barH / 2 + 4) + '" text-anchor="end" fill="#9ca0ab" font-size="11">' + (d[labelKey] || '') + '</text>';
    // track
    svg += '<rect x="' + labelW + '" y="' + y + '" width="' + (width - labelW - 10) + '" height="' + barH + '" rx="4" fill="#232733"/>';
    // fill
    svg += '<rect x="' + labelW + '" y="' + y + '" width="' + bw + '" height="' + barH + '" rx="4" fill="' + color + '" opacity="0.85"/>';
    // value
    svg += '<text x="' + (labelW + bw + 8) + '" y="' + (y + barH / 2 + 4) + '" fill="#e4e6eb" font-size="11" font-weight="600">' + fmtNum(val) + '</text>';
  });
  svg += '</svg>';
  return svg;
}

/* ─── Line/Area-style bar chart for time series ── */
function timeBarChart(data, labelKey, valueKey, color, width, height) {
  if (!data || data.length === 0) return '<div class="empty">No data</div>';
  const max = Math.max(...data.map(d => d[valueKey] || 0), 1);
  const padL = 10, padR = 10, padT = 10, padB = 30;
  const usableW = width - padL - padR;
  const usableH = height - padT - padB;
  const barW = Math.max(4, Math.floor(usableW / data.length) - 4);

  let svg = '<svg class="chart" width="' + width + '" height="' + height + '" viewBox="0 0 ' + width + ' ' + height + '">';
  // grid lines
  for (let i = 0; i <= 4; i++) {
    const y = padT + (usableH / 4) * i;
    svg += '<line x1="' + padL + '" y1="' + y + '" x2="' + (width - padR) + '" y2="' + y + '" stroke="#2d3140" stroke-width="1"/>';
    const gridVal = Math.round(max - (max / 4) * i);
    svg += '<text x="' + padL + '" y="' + (y - 4) + '" fill="#6b7080" font-size="9">' + fmtNum(gridVal) + '</text>';
  }
  data.forEach((d, i) => {
    const x = padL + (usableW / data.length) * i + 2;
    const v = d[valueKey] || 0;
    const bh = Math.max(1, (v / max) * usableH);
    const y = padT + usableH - bh;
    svg += '<rect x="' + x + '" y="' + y + '" width="' + barW + '" height="' + bh + '" rx="3" fill="' + color + '" opacity="0.8">';
    svg += '<title>' + (d[labelKey] || '') + ': ' + fmtNum(v) + '</title></rect>';
    // Bottom label (every other or all if few)
    if (data.length <= 14 || i % 2 === 0) {
      let label = d[labelKey] || '';
      if (label.length > 10) label = label.slice(5, 10);
      svg += '<text x="' + (x + barW/2) + '" y="' + (padT + usableH + 16) + '" text-anchor="middle" fill="#6b7080" font-size="9">' + label + '</text>';
    }
  });
  svg += '</svg>';
  return svg;
}

/* ─── Horizontal stacked bars ──────────────────── */
function horizontalBars(items, color) {
  if (!items || items.length === 0) return '<div class="empty">No data</div>';
  const max = Math.max(...items.map(d => d.value), 1);
  let html = '';
  items.forEach(d => {
    const pct = Math.max(1, (d.value / max) * 100);
    html += '<div class="bar-row">';
    html += '  <div class="bar-label" title="' + d.label + '">' + d.label + '</div>';
    html += '  <div class="bar-track">';
    html += '    <div class="bar-fill" style="width:' + pct + '%;background:' + (d.color || color) + '"></div>';
    html += '    <div class="bar-val">' + fmtNum(d.value) + '</div>';
    html += '  </div>';
    html += '</div>';
  });
  return html;
}

/* ─── Data Loading ──────────────────────────────── */
async function loadAll() {
  const btn = document.getElementById('btnRefresh');
  btn.disabled = true;
  btn.textContent = 'Loading...';
  try {
    const [stats, health, statuses, fairness, hourly, users, docs, logs, activity] = await Promise.all([
      api('stats'),
      api('health'),
      api('document-statuses'),
      api('fairness-distribution'),
      api('hourly'),
      api('users'),
      api('documents'),
      api('logs?limit=50'),
      api('activity?limit=40'),
    ]);
    renderOverview(stats, health, statuses, fairness);
    renderLLM(stats, hourly, logs);
    renderUsers(users);
    renderDocs(docs);
    renderActivity(activity);
    document.getElementById('lastUpdated').textContent = 'Updated ' + new Date().toLocaleTimeString();
    document.getElementById('errorBanner').style.display = 'none';
  } catch (e) {
    showError(e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Refresh';
  }
}

/* ─── Renderers ─────────────────────────────────── */

function renderOverview(stats, health, statuses, fairness) {
  const o = stats.overall;
  const h = health;

  // KPI cards
  document.getElementById('kpiGrid').innerHTML = `
    <div class="kpi"><div class="kpi-label">Total Users</div><div class="kpi-value accent">${fmtNum(h.total_users)}</div><div class="kpi-sub">${fmtNum(h.active_users_7d)} active (7d)</div></div>
    <div class="kpi"><div class="kpi-label">Documents</div><div class="kpi-value cyan">${fmtNum(h.total_documents)}</div><div class="kpi-sub">${fmtNum(h.error_documents)} in error state</div></div>
    <div class="kpi"><div class="kpi-label">Chat Messages</div><div class="kpi-value pink">${fmtNum(h.total_chat_messages)}</div></div>
    <div class="kpi"><div class="kpi-label">LLM Calls</div><div class="kpi-value">${fmtNum(o.total_calls)}</div><div class="kpi-sub">${fmtNum(h.llm_calls_24h)} in last 24h</div></div>
    <div class="kpi"><div class="kpi-label">Total Tokens</div><div class="kpi-value">${fmtNum(o.total_tokens)}</div></div>
    <div class="kpi"><div class="kpi-label">Total LLM Cost</div><div class="kpi-value amber">${fmtCost(o.total_cost_usd)}</div></div>
    <div class="kpi"><div class="kpi-label">Success Rate</div><div class="kpi-value ${o.success_rate >= 95 ? 'green' : o.success_rate >= 80 ? 'amber' : 'red'}">${fmtPct(o.success_rate)}</div></div>
    <div class="kpi"><div class="kpi-label">Avg Response</div><div class="kpi-value">${fmtMs(o.avg_response_ms)}</div></div>
  `;

  // Daily chart
  const chartWidth = Math.min(600, window.innerWidth - 100);
  document.getElementById('dailyChart').innerHTML = timeBarChart(stats.daily, 'date', 'calls', '#6366f1', chartWidth, 180);

  // Module chart
  const moduleColors = { sla_extraction: '#6366f1', chat: '#06b6d4', vin_pricing: '#ec4899' };
  const moduleItems = stats.modules.map(m => ({
    label: m.module, value: m.calls, color: moduleColors[m.module] || '#818cf8'
  }));
  document.getElementById('moduleChart').innerHTML = horizontalBars(moduleItems, '#6366f1');

  // Document status chart
  const statusColors = { ready: '#22c55e', pending: '#f59e0b', processing: '#f59e0b', extraction_complete: '#06b6d4', sla_failed: '#ef4444', error: '#ef4444' };
  const statusItems = Object.entries(statuses).map(([k,v]) => ({
    label: k, value: v, color: statusColors[k] || '#818cf8'
  }));
  document.getElementById('statusChart').innerHTML = horizontalBars(statusItems, '#6366f1');

  // Fairness distribution
  const fairnessItems = fairness.map(f => ({
    label: f.range, value: f.count, color: '#22c55e'
  }));
  document.getElementById('fairnessChart').innerHTML = fairnessItems.length
    ? horizontalBars(fairnessItems, '#22c55e')
    : '<div class="empty">No scored documents yet</div>';
}

function renderLLM(stats, hourly, logs) {
  // Hourly chart
  const hourlyData = hourly.map(h => ({
    ...h,
    label: h.hour ? h.hour.slice(11, 16) : '',
  }));
  const chartWidth = Math.min(600, window.innerWidth - 100);
  document.getElementById('hourlyChart').innerHTML = timeBarChart(hourlyData, 'label', 'calls', '#06b6d4', chartWidth, 180);

  // Module table
  const modules = stats.modules;
  let mt = '<table><thead><tr><th>Module</th><th>Calls</th><th>Tokens</th><th>Avg Latency</th><th>Errors</th></tr></thead><tbody>';
  modules.forEach(m => {
    mt += '<tr>';
    mt += '<td><strong>' + m.module + '</strong></td>';
    mt += '<td>' + fmtNum(m.calls) + '</td>';
    mt += '<td>' + fmtNum(m.tokens) + '</td>';
    mt += '<td>' + fmtMs(m.avg_ms) + '</td>';
    mt += '<td>' + (m.errors > 0 ? '<span style="color:var(--red)">' + m.errors + '</span>' : '0') + '</td>';
    mt += '</tr>';
  });
  mt += '</tbody></table>';
  document.getElementById('moduleTable').innerHTML = modules.length ? mt : '<div class="empty">No data</div>';

  // Logs table
  let lt = '<table><thead><tr><th>Time</th><th>Module</th><th>Model</th><th>Tokens</th><th>Latency</th><th>Cost</th><th>Status</th><th>Error</th></tr></thead><tbody>';
  logs.forEach(l => {
    lt += '<tr>';
    lt += '<td>' + fmtTime(l.timestamp) + '</td>';
    lt += '<td>' + l.module + '</td>';
    lt += '<td class="mono">' + (l.model || '-') + '</td>';
    lt += '<td>' + fmtNum(l.total_tokens) + '</td>';
    lt += '<td>' + fmtMs(l.response_time_ms) + '</td>';
    lt += '<td>' + fmtCost(l.cost_usd) + '</td>';
    lt += '<td>' + (l.success ? '<span class="status-dot ok"></span>' : '<span class="status-dot err"></span>') + '</td>';
    lt += '<td class="truncate" title="' + (l.error_message || '') + '">' + (l.error_message || '-') + '</td>';
    lt += '</tr>';
  });
  lt += '</tbody></table>';
  document.getElementById('logsTable').innerHTML = logs.length ? lt : '<div class="empty">No logs yet</div>';
}

function renderUsers(users) {
  if (!users || users.length === 0) {
    document.getElementById('usersTable').innerHTML = '<div class="empty">No users</div>';
    return;
  }
  let html = '<table><thead><tr><th>Email</th><th>Name</th><th>Joined</th><th>Active</th><th>Docs</th><th>Chats</th><th>LLM Calls</th><th>Tokens</th><th>Cost</th></tr></thead><tbody>';
  users.forEach(u => {
    html += '<tr>';
    html += '<td><strong>' + u.email + '</strong></td>';
    html += '<td>' + (u.full_name || '-') + '</td>';
    html += '<td>' + fmtDate(u.created_at) + '</td>';
    html += '<td>' + (u.is_active ? '<span class="status-dot ok"></span>' : '<span class="status-dot err"></span>') + '</td>';
    html += '<td>' + fmtNum(u.doc_count) + '</td>';
    html += '<td>' + fmtNum(u.chat_count) + '</td>';
    html += '<td>' + fmtNum(u.llm_calls) + '</td>';
    html += '<td>' + fmtNum(u.total_tokens) + '</td>';
    html += '<td>' + fmtCost(u.total_cost) + '</td>';
    html += '</tr>';
  });
  html += '</tbody></table>';
  document.getElementById('usersTable').innerHTML = html;
}

function renderDocs(docs) {
  if (!docs || docs.length === 0) {
    document.getElementById('docsTable').innerHTML = '<div class="empty">No documents</div>';
    return;
  }
  let html = '<table><thead><tr><th>Filename</th><th>User</th><th>Status</th><th>Fairness</th><th>VIN</th><th>Uploaded</th><th>Retries</th><th>Error</th></tr></thead><tbody>';
  docs.forEach(d => {
    const sc = d.fairness_score != null ? d.fairness_score.toFixed(0) : '-';
    html += '<tr>';
    html += '<td class="truncate" title="' + d.filename + '">' + d.filename + '</td>';
    html += '<td>' + d.user_email + '</td>';
    html += '<td>' + statusPill(d.status) + '</td>';
    html += '<td class="' + scoreClass(d.fairness_score) + '"><strong>' + sc + '</strong></td>';
    html += '<td class="mono">' + (d.vin || '-') + '</td>';
    html += '<td>' + fmtTime(d.uploaded_at) + '</td>';
    html += '<td>' + d.retry_count + '</td>';
    html += '<td class="truncate" title="' + (d.error || '') + '">' + (d.error || '-') + '</td>';
    html += '</tr>';
  });
  html += '</tbody></table>';
  document.getElementById('docsTable').innerHTML = html;
}

function renderActivity(activity) {
  if (!activity || activity.length === 0) {
    document.getElementById('activityTable').innerHTML = '<div class="empty">No activity yet</div>';
    return;
  }
  let html = '<table><thead><tr><th>Time</th><th>Type</th><th>Actor</th><th>Detail</th></tr></thead><tbody>';
  activity.forEach(a => {
    html += '<tr>';
    html += '<td>' + fmtTime(a.timestamp) + '</td>';
    html += '<td><span class="activity-type ' + a.type + '">' + a.type + '</span></td>';
    html += '<td>' + a.actor + '</td>';
    html += '<td class="truncate" title="' + (a.detail || '') + '">' + (a.detail || '-') + '</td>';
    html += '</tr>';
  });
  html += '</tbody></table>';
  document.getElementById('activityTable').innerHTML = html;
}

/* ─── Init ──────────────────────────────────────── */
loadAll();
// Auto-refresh every 60 seconds
setInterval(loadAll, 60000);
</script>
</body>
</html>"""
