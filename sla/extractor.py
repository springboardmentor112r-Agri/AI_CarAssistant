"""
sla/extractor.py
================
Tab 1: SLA Extractor UI
Upload a PDF or image → Gemini extracts SLA data → stored in session state.
"""

import json
import base64
import streamlit as st
from google import genai
from google.genai import types


# ── Gemini client ──────────────────────────────────────────────────────────────
def _get_client() -> genai.Client:
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])


# ── Extraction prompt ──────────────────────────────────────────────────────────
_PROMPT = """
You are an expert SLA / lease-agreement parser.

Extract ALL relevant fields from the uploaded document and return ONLY valid JSON
(no markdown fences, no explanation) matching this exact schema:

{
  "parties": {
    "lessee_name":  "",
    "lessor_name":  "",
    "lessee_email": "",
    "lessor_email": "",
    "lessee_phone": "",
    "lessor_phone": ""
  },
  "vehicle": {
    "brand":   "",
    "model":   "",
    "year":    "",
    "vin":     "",
    "color":   "",
    "mileage": ""
  },
  "lease_terms": {
    "start_date":         "",
    "end_date":           "",
    "duration_months":    0,
    "annual_mileage":     "",
    "excess_mileage_fee": ""
  },
  "financial": {
    "monthly_payment":   "",
    "security_deposit":  "",
    "down_payment":      "",
    "total_lease_value": "",
    "currency":          "INR"
  },
  "sla_terms": {
    "service_tier":            "",
    "uptime_guarantee":        "",
    "response_time":           "",
    "support_hours":           "",
    "penalty_clause":          "",
    "renewal_option":          "",
    "termination_notice_days": 0
  }
}

Rules:
- Use empty string "" for text fields that are missing.
- Use 0 for numeric fields that are missing.
- Do NOT include any text outside the JSON object.
"""


# ── Call Gemini ────────────────────────────────────────────────────────────────
def _extract_with_gemini(file_bytes: bytes, mime_type: str) -> dict:
    client = _get_client()
    b64    = base64.standard_b64encode(file_bytes).decode("utf-8")

    response = client.models.generate_content(
        model    = "gemini-2.5-flash",
        contents = [
            types.Part(
                inline_data=types.Blob(mime_type=mime_type, data=b64)
            ),
            types.Part(text=_PROMPT),
        ],
    )

    raw = response.text.strip()
    # Strip accidental markdown fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


# ── UI helpers ─────────────────────────────────────────────────────────────────
def _row(label: str, value: str, highlight: bool = False):
    color  = "#F97316" if highlight else "#E2E8F0"
    weight = "700"     if highlight else "400"
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;
                padding:.45rem .9rem;border-bottom:1px solid rgba(249,115,22,.07);
                font-size:.84rem;">
        <span style="color:#94A3B8;font-weight:500;">{label}</span>
        <span style="color:{color};font-weight:{weight};">{value or "—"}</span>
    </div>""", unsafe_allow_html=True)


def _card_open(title: str):
    st.markdown(f"""
    <div class="lease-card">
        <div class="card-title">{title}</div>""", unsafe_allow_html=True)


def _card_close():
    st.markdown("</div>", unsafe_allow_html=True)


def _render_extracted_data(data: dict):
    """Display extracted SLA data in styled cards."""
    col1, col2 = st.columns(2)

    with col1:
        p = data.get("parties", {})
        _card_open("👥 Parties")
        _row("Lessee",       p.get("lessee_name"),  highlight=True)
        _row("Lessor",       p.get("lessor_name"),  highlight=True)
        _row("Lessee Email", p.get("lessee_email"))
        _row("Lessor Email", p.get("lessor_email"))
        _row("Lessee Phone", p.get("lessee_phone"))
        _row("Lessor Phone", p.get("lessor_phone"))
        _card_close()

        f = data.get("financial", {})
        _card_open("💰 Financial")
        _row("Monthly Payment",   f.get("monthly_payment"),  highlight=True)
        _row("Security Deposit",  f.get("security_deposit"))
        _row("Down Payment",      f.get("down_payment"))
        _row("Total Lease Value", f.get("total_lease_value"))
        _row("Currency",          f.get("currency"))
        _card_close()

    with col2:
        v = data.get("vehicle", {})
        _card_open("🚗 Vehicle")
        _row("Brand",   v.get("brand"),  highlight=True)
        _row("Model",   v.get("model"),  highlight=True)
        _row("Year",    v.get("year"))
        _row("VIN",     v.get("vin"))
        _row("Color",   v.get("color"))
        _row("Mileage", v.get("mileage"))
        _card_close()

        lt = data.get("lease_terms", {})
        _card_open("📅 Lease Terms")
        _row("Start Date",         lt.get("start_date"))
        _row("End Date",           lt.get("end_date"))
        _row("Duration (months)",  lt.get("duration_months"), highlight=True)
        _row("Annual Mileage",     lt.get("annual_mileage"))
        _row("Excess Mileage Fee", lt.get("excess_mileage_fee"))
        _card_close()

    # SLA Terms — full width
    s = data.get("sla_terms", {})
    if any(str(v) for v in s.values() if v):
        st.markdown('<div class="lease-card"><div class="card-title">🛡️ SLA Terms</div>',
                    unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            _row("Service Tier",     s.get("service_tier"),     highlight=True)
            _row("Uptime Guarantee", s.get("uptime_guarantee"))
            _row("Response Time",    s.get("response_time"))
            _row("Support Hours",    s.get("support_hours"))
        with c2:
            _row("Penalty Clause",          s.get("penalty_clause"))
            _row("Renewal Option",          s.get("renewal_option"))
            _row("Termination Notice Days", s.get("termination_notice_days"))
        st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# Main render function (called from app.py)
# ══════════════════════════════════════════════════════════════════════════════
def render_sla_tab():
    st.markdown("""
    <div class="lease-card">
        <div class="card-title">📄 Upload Lease / SLA Document</div>
        <p style="color:#94A3B8;font-size:.85rem;margin:0;">
            Upload a PDF or image of your car lease or SLA agreement.
            Gemini will automatically extract all key fields.
        </p>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Choose a file",
        type=["pdf", "png", "jpg", "jpeg", "webp"],
        key="sla_upload",
        label_visibility="collapsed",
    )

    # Reset state when a new file is chosen
    if uploaded and uploaded.name != st.session_state.get("current_file", ""):
        st.session_state["extraction_done"] = False
        st.session_state["sla_data"]        = None
        st.session_state["current_file"]    = uploaded.name

    if uploaded:
        st.markdown(f"""
        <div style="font-size:.82rem;color:#64748B;margin:.4rem 0 .8rem;">
            📎 {uploaded.name} &nbsp;·&nbsp; {uploaded.size / 1024:.1f} KB
        </div>""", unsafe_allow_html=True)

        if not st.session_state.get("extraction_done"):
            if st.button("🔍  Extract SLA Data", use_container_width=True):
                with st.spinner("Sending to Gemini — extracting SLA fields…"):
                    try:
                        file_bytes = uploaded.read()
                        mime_type  = uploaded.type or "application/octet-stream"
                        data = _extract_with_gemini(file_bytes, mime_type)

                        st.session_state["sla_data"]        = data
                        st.session_state["extraction_done"] = True
                        st.rerun()

                    except json.JSONDecodeError as e:
                        st.error(f"Gemini returned invalid JSON — try again. Detail: {e}")
                    except Exception as e:
                        st.error(f"Extraction failed: {e}")
        else:
            st.markdown('<div class="alert-ok">✅ Extraction complete — review fields below.</div>',
                        unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            data = st.session_state["sla_data"]
            _render_extracted_data(data)

            st.markdown("<br>", unsafe_allow_html=True)
            col_save, col_reset = st.columns([2, 1])

            with col_save:
                if st.button("💾  Save to Contracts", use_container_width=True):
                    saved = st.session_state.get("saved_contracts", [])
                    if data not in saved:
                        saved.append(data)
                        st.session_state["saved_contracts"] = saved
                        st.success("Saved! Switch to the SLA Contract tab to manage it.")
                    else:
                        st.info("This contract is already saved.")

            with col_reset:
                if st.button("🔄  Re-extract", use_container_width=True):
                    st.session_state["extraction_done"] = False
                    st.session_state["sla_data"]        = None
                    st.rerun()
    else:
        st.markdown("""
        <div style="text-align:center;padding:3rem 1rem;color:#475569;">
            <div style="font-size:3rem;">📂</div>
            <div style="margin-top:.5rem;font-size:.9rem;">
                No file selected — upload a PDF or image above to get started.
            </div>
        </div>""", unsafe_allow_html=True)
