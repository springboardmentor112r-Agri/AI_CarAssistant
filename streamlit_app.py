"""
streamlit_app.py  —  Car Lease Analyzer
Public app: Sign In / Sign Up for all users.
Exactly 4 tabs as shown in the video:
  📄 Extract SLA  |  🔍 VIN Report  |  💬 Negotiate 
"""

import streamlit as st
import time
from dotenv import load_dotenv
import os

# ── Module imports with graceful fallbacks ────────────────────────────────────
try:
    from auth.user_auth import (
        init_auth_session, render_auth_page, render_user_profile
    )
    AUTH_OK = True
except ImportError:
    AUTH_OK = False
    def init_auth_session(): pass
    def render_auth_page(): st.error("Auth module missing")
    def render_user_profile(): pass

try:
    from sla.extractor import render_sla_tab
except ImportError:
    def render_sla_tab(): st.error("SLA module missing")

try:
    from vin.report import render_vin_tab
except ImportError:
    def render_vin_tab(): st.error("VIN module missing")

try:
    from negotiate.advisor import render_negotiate_tab
except ImportError:
    def render_negotiate_tab(): st.error("Negotiate module missing")

try:
    from compare.contracts import render_compare_tab
except ImportError:
    def render_compare_tab(): st.error("Compare module missing")

load_dotenv()

# ─── Theme ────────────────────────────────────────────────────────────────────
def apply_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

    *, *::before, *::after { font-family: 'Inter', sans-serif; box-sizing: border-box; }

    /* ── App background ── */
    .stApp {
        background: linear-gradient(135deg, #0F172A 0%, #1E1533 50%, #0F172A 100%);
        background-attachment: fixed;
        color: #F1F5F9;
    }
    .stApp::before {
        content: '';
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background:
            radial-gradient(circle at 15% 50%, rgba(249,115,22,.055) 0%, transparent 55%),
            radial-gradient(circle at 85% 15%, rgba(249,115,22,.04)  0%, transparent 55%);
        pointer-events: none; z-index: 0;
    }

    /* ── Header bar ── */
    .app-header {
        background: rgba(15,23,42,.97);
        border-bottom: 3px solid #F97316;
        padding: 0 2rem;
        height: 68px;
        display: flex; align-items: center; justify-content: space-between;
        box-shadow: 0 4px 24px rgba(249,115,22,.18);
        position: relative;
    }
    .app-header::after {
        content: '';
        position: absolute; bottom: -3px; left: 0; width: 100%; height: 3px;
        background: linear-gradient(90deg, transparent, #F97316 30%, #EA580C 70%, transparent);
    }
    .hdr-brand { display: flex; align-items: center; gap: .7rem; }
    .hdr-logo {
        width: 40px; height: 40px;
        background: linear-gradient(135deg, #F97316, #EA580C);
        border-radius: 10px; display: flex; align-items: center;
        justify-content: center; font-size: 1.3rem;
        box-shadow: 0 0 16px rgba(249,115,22,.4);
    }
    .hdr-title  { font-size: 1.25rem; font-weight: 800; color: #F1F5F9; line-height: 1.1; }
    .hdr-sub    { font-size: .7rem;  color: #94A3B8; }
    .hdr-user   { display: flex; align-items: center; gap: .6rem; }
    .hdr-hi     { color: #94A3B8; font-size: .85rem; }
    .hdr-name   { color: #F97316; font-weight: 700; }
    .hdr-signout {
        background: transparent; border: 1.5px solid rgba(249,115,22,.5);
        color: #F97316; border-radius: 8px; padding: .35rem .9rem;
        font-size: .82rem; font-weight: 600; cursor: pointer;
        transition: all .2s;
    }
    .hdr-signout:hover {
        background: rgba(249,115,22,.1); border-color: #F97316;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(15,23,42,.92);
        border-bottom: 2px solid rgba(249,115,22,.25);
        gap: 0; padding: 0;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 0; padding: .95rem 1.6rem;
        font-size: .88rem; font-weight: 600; color: #64748B;
        border-bottom: 3px solid transparent;
        transition: all .18s;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #F97316; background: rgba(249,115,22,.05); }
    .stTabs [aria-selected="true"] {
        color: #F97316 !important;
        border-bottom: 3px solid #F97316 !important;
        background: rgba(249,115,22,.07) !important;
    }

    /* ── Generic card ── */
    .lease-card {
        background: linear-gradient(135deg,rgba(30,41,59,.85),rgba(15,23,42,.92));
        border: 1px solid rgba(249,115,22,.22);
        border-radius: 14px; padding: 1.4rem;
        box-shadow: 0 4px 20px rgba(0,0,0,.28);
        margin: .75rem 0; transition: all .25s;
    }
    .lease-card:hover {
        border-color: rgba(249,115,22,.45);
        box-shadow: 0 6px 28px rgba(249,115,22,.12);
        transform: translateY(-2px);
    }
    .card-title {
        font-size: .88rem; font-weight: 700; color: #F97316;
        text-transform: uppercase; letter-spacing: .8px;
        border-left: 3px solid #F97316; padding-left: .65rem;
        margin-bottom: .85rem;
    }

    /* ── Metric cards ── */
    .metric-card {
        background: rgba(30,41,59,.9);
        border: 1px solid rgba(249,115,22,.28);
        border-radius: 12px; padding: 1.2rem; text-align: center;
        transition: all .25s;
    }
    .metric-card:hover {
        border-color: rgba(249,115,22,.55);
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(249,115,22,.15);
    }
    .metric-value {
        font-size: 1.9rem; font-weight: 900;
        background: linear-gradient(135deg,#F97316,#EA580C);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
        font-family: 'JetBrains Mono', monospace;
    }
    .metric-label {
        font-size: .7rem; color: #94A3B8; font-weight: 600;
        text-transform: uppercase; letter-spacing: 1.2px; margin-top: .2rem;
    }
    .metric-icon { font-size: 1.6rem; margin-bottom: .4rem; }

    /* ── Upload zone ── */
    .upload-zone {
        background: rgba(30,41,59,.45);
        border: 2px dashed rgba(249,115,22,.45);
        border-radius: 14px; padding: 3rem 2rem; text-align: center;
        transition: all .25s;
    }
    .upload-zone:hover {
        border-color: #F97316; background: rgba(249,115,22,.05);
    }

    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, #F97316, #EA580C);
        color: #fff; border: none; border-radius: 10px;
        padding: .68rem 1.8rem; font-weight: 700; font-size: .92rem;
        letter-spacing: .3px; transition: all .25s;
        box-shadow: 0 4px 14px rgba(249,115,22,.3);
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #EA580C, #C2410C);
        box-shadow: 0 6px 22px rgba(249,115,22,.45);
        transform: translateY(-2px);
    }
    .stDownloadButton > button {
        background: rgba(30,41,59,.9) !important;
        color: #F97316 !important; border: 1px solid rgba(249,115,22,.4) !important;
        box-shadow: none !important;
    }
    .stDownloadButton > button:hover {
        border-color: #F97316 !important;
        background: rgba(249,115,22,.08) !important;
        transform: translateY(-1px);
    }

    /* ── KV table ── */
    .kv-table { width: 100%; border-collapse: collapse; }
    .kv-table td {
        padding: .5rem .9rem; font-size: .86rem;
        border-bottom: 1px solid rgba(249,115,22,.08);
    }
    .kv-table td:first-child { color: #94A3B8; width: 42%; font-weight: 500; }
    .kv-table td:last-child  { color: #E2E8F0; }
    .kv-table tr:last-child td { border-bottom: none; }

    /* ── Section divider ── */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #F97316, transparent);
        margin: 1.25rem 0;
        box-shadow: 0 0 6px rgba(249,115,22,.25);
    }

    /* ── Alerts ── */
    .alert-ok   { background:rgba(34,197,94,.1);  border:1px solid rgba(34,197,94,.35);
                  border-radius:9px; padding:.65rem 1rem; color:#86EFAC; font-size:.87rem; }
    .alert-warn { background:rgba(245,158,11,.1); border:1px solid rgba(245,158,11,.35);
                  border-radius:9px; padding:.65rem 1rem; color:#FDE68A; font-size:.87rem; }
    .alert-err  { background:rgba(239,68,68,.1);  border:1px solid rgba(239,68,68,.35);
                  border-radius:9px; padding:.65rem 1rem; color:#FCA5A5; font-size:.87rem; }
    .alert-info { background:rgba(249,115,22,.1); border:1px solid rgba(249,115,22,.3);
                  border-radius:9px; padding:.65rem 1rem; color:#FED7AA; font-size:.87rem; }

    /* ── Progress bar ── */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #F97316, #EA580C);
        box-shadow: 0 0 8px rgba(249,115,22,.45);
    }

    /* ── File uploader ── */
    [data-testid="stFileUploader"] {
        background: rgba(30,41,59,.4);
        border: 2px dashed rgba(249,115,22,.38); border-radius: 12px; padding: .8rem;
    }

    /* ── Inputs ── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(30,41,59,.8);
        border: 1px solid rgba(249,115,22,.3);
        border-radius: 10px; color: #F1F5F9;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #F97316;
        box-shadow: 0 0 0 2px rgba(249,115,22,.18);
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg,#0F172A,#1E293B);
        border-right: 2px solid rgba(249,115,22,.28);
    }

    /* ── Metrics ── */
    [data-testid="stMetricValue"] { font-family:'JetBrains Mono',monospace; color:#F97316; font-weight:800; }
    [data-testid="stMetricLabel"] { color:#94A3B8; font-weight:600; }

    /* ── Chat bubbles ── */
    .chat-user {
        background: linear-gradient(135deg,#F97316,#EA580C);
        color: #fff; border-radius: 18px 18px 4px 18px;
        padding: .7rem 1rem; max-width: 78%; margin-left: auto;
        margin-bottom: .65rem; font-size: .88rem;
        box-shadow: 0 2px 10px rgba(249,115,22,.3);
    }
    .chat-bot {
        background: rgba(30,41,59,.95);
        border: 1px solid rgba(249,115,22,.18);
        color: #E2E8F0; border-radius: 18px 18px 18px 4px;
        padding: .7rem 1rem; max-width: 84%;
        margin-bottom: .65rem; font-size: .88rem;
        box-shadow: 0 2px 8px rgba(0,0,0,.25);
        line-height: 1.6;
    }

    /* ── VIN counter orange when full ── */
    .vin-full { color: #F97316 !important; font-weight: 700; }

    /* ── Compare contract row ── */
    .contract-row {
        background: rgba(30,41,59,.7);
        border: 1.5px solid rgba(249,115,22,.18);
        border-radius: 13px; padding: 1rem 1.2rem;
        transition: all .18s; margin-bottom: .6rem;
    }
    .contract-row.selected {
        border-color: #F97316;
        background: rgba(249,115,22,.07);
        box-shadow: 0 0 16px rgba(249,115,22,.12);
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 7px; height: 7px; }
    ::-webkit-scrollbar-track { background: #0F172A; border-radius: 8px; }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg,#F97316,#EA580C);
        border-radius: 8px;
    }

    /* ── Footer ── */
    .footer {
        text-align: center; padding: 1.2rem;
        color: #475569; font-size: .78rem;
        border-top: 1px solid rgba(249,115,22,.15);
        margin-top: 2.5rem;
    }
    </style>
    """, unsafe_allow_html=True)


# ─── Header ───────────────────────────────────────────────────────────────────
def render_header():
    name = st.session_state.get("display_name", "User")
    st.markdown(f"""
    <div class="app-header">
        <div class="hdr-brand">
            <div class="hdr-logo">🚗</div>
            <div>
                <div class="hdr-title">Car Lease Analyzer</div>
                <div class="hdr-sub">AI-powered lease contract analysis &amp; negotiation</div>
            </div>
        </div>
        <div class="hdr-user">
            <span class="hdr-hi">Hi, <span class="hdr-name">{name}</span></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Sign Out in same row via sidebar button — keep header clean
    with st.sidebar:
        render_user_profile()
    

        


# ─── Shared helpers ───────────────────────────────────────────────────────────
def show_metrics(data: dict):
    """Render a row of orange metric cards."""
    cols = st.columns(min(len(data), 4))
    for i, (_, d) in enumerate(data.items()):
        with cols[i % len(cols)]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">{d.get('icon','📊')}</div>
                <div class="metric-value">{d.get('value','—')}</div>
                <div class="metric-label">{d.get('label','')}</div>
            </div>""", unsafe_allow_html=True)


def show_progress(msg: str, secs: float = 1.5):
    st.markdown(f"""
    <div style="text-align:center;margin:1.2rem 0;">
        <span style="color:#F97316;font-weight:700;font-size:.9rem;letter-spacing:1.5px;">
            🚗 {msg}…
        </span>
    </div>""", unsafe_allow_html=True)
    bar = st.progress(0)
    for i in range(100):
        bar.progress(i + 1)
        time.sleep(secs / 100)
    bar.empty()


def show_success(title: str, detail: str = ""):
    det = f"<br><span style='font-size:.82rem;opacity:.85;'>{detail}</span>" if detail else ""
    st.markdown(f"""
    <div class="alert-ok" style="text-align:center;padding:.8rem 1rem;border-radius:10px;margin:.75rem 0;">
        <strong>✓ {title}</strong>{det}
    </div>""", unsafe_allow_html=True)


# ─── Session defaults ─────────────────────────────────────────────────────────
def init_session():
    defaults = {
        "authenticated":    False,
        "username":         "",
        "display_name":     "",
        "auth_mode":        "signin",
        "auth_error":       "",
        "auth_success":     "",
        "sla_data":         None,
        "current_file":     None,
        "extraction_done":  False,
        "sla_view":         "table",
        "chat_history":     [],
        "saved_contracts":  [],
        "compare_sel":      [],
        "show_compare":     False,
        "vin_info":         None,
        "vin_recalls":      None,
        "vin_queried":      "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    init_session()
    init_auth_session()

    st.set_page_config(
        page_title="🚗 Car Lease Analyzer",
        page_icon="🚗",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    apply_theme()

    # ── Auth gate ──────────────────────────────────────────────────────────
    if not st.session_state.authenticated:
        render_auth_page()
        return

    # ── Authenticated layout ───────────────────────────────────────────────
    render_header()

    n = len(st.session_state.compare_sel)
    compare_label = f"📊 Compare {'(' + str(n) + ')' if n else ''}"

    tab1, tab2, tab3 = st.tabs([
        "📄 Extract SLA",
        "🔍 VIN Report",
        "💬 Negotiate",
        # compare_label,
    ])

    with tab1:
        render_sla_tab()
    with tab2:
        render_vin_tab()
    with tab3:
        render_negotiate_tab()
    # with tab4:
    #     render_compare_tab()

    st.markdown("""
    <div class="divider" style="margin-top:2.5rem;"></div>
    <div class="footer">🚗 Car Lease Analyzer &nbsp;•&nbsp; AI-Powered Lease Intelligence
    &nbsp;•&nbsp; Developed by S-A-M</div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
