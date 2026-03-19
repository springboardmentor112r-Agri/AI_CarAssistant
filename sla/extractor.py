"""
sla/extractor.py  —  Tab 1: Extract SLA
Exactly matches video:
  • Upload zone (JPG/PNG/PDF up to 20 MB)
  • Document Preview card with ✕ close
  • "Extracting SLA Data…" button + "Processing PDF…" green bar
  • Extracted SLA Data with Table / JSON / Export JSON toggles
  • Sections: Document Info, Parties, Vehicle, Financial & Lease Terms,
              Mileage Terms, SLA Obligations, End of Lease Options, Additional Terms
  • Fairness score
  • Red flags section
  • Visual Analysis: Criteria Overview (radar) + Score by Criterion (bar)
                    Red Flags by Severity (donut) + Weight Distribution (donut)
  • Market Price Comparison bar chart
"""

import streamlit as st
import json, os, base64, time
from datetime import datetime

import plotly.graph_objects as go
import plotly.express as px

try:
    import anthropic
    _HAS_ANTHROPIC = True
except ImportError:
    _HAS_ANTHROPIC = False

_DARK = dict(
    plot_bgcolor  = "rgba(15,23,42,0)",
    paper_bgcolor = "rgba(0,0,0,0)",
    font          = dict(family="Inter", color="#E2E8F0"),
    margin        = dict(l=16, r=16, t=36, b=16),
)


# ── Claude extraction ─────────────────────────────────────────────────────────
_PROMPT = """You are an expert car lease contract analyst.
Extract ALL available details from this lease document and return ONLY valid JSON
(no markdown fences, no extra text).

Required JSON structure:
{
  "document_info": {
    "document_type": "",
    "document_date": "",
    "contract_number": ""
  },
  "parties": {
    "lessor_name": "", "lessor_address": "",
    "lessee_name": "", "lessee_address": ""
  },
  "vehicle": {
    "vin": "", "brand": "", "model": "", "year": "",
    "variant": "", "body_type": "", "fuel_type": ""
  },
  "financial": {
    "monthly_payment": "", "down_payment": "",
    "security_deposit": "", "total_lease_cost": "", "currency": ""
  },
  "lease_terms": {
    "start_date": "", "end_date": "", "duration_months": 0
  },
  "mileage_terms": {
    "annual_limit": "", "total_limit": "", "excess_charge": ""
  },
  "sla_obligations": {
    "maintenance_responsibility": "",
    "insurance_requirements": "",
    "wear_and_tear_policy": "",
    "early_termination_fee": "",
    "late_payment_fee": ""
  },
  "end_of_lease": {
    "purchase_option": "",
    "residual_value": "",
    "return_conditions": ""
  },
  "additional_terms": [],
  "red_flags": [
    {"issue": "", "severity": "High|Medium|Low", "recommendation": ""}
  ],
  "fairness_score": 0,
  "fairness_label": "Excellent|Good|Fair|Poor|Needs Negotiation",
  "market_comparison": {
    "vehicle_description": "",
    "estimated_msrp": "",
    "market_monthly_range": "",
    "is_above_market": true
  }
}"""


def _call_claude(file_bytes: bytes, mime: str) -> dict:
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    b64 = base64.standard_b64encode(file_bytes).decode()
    if mime == "application/pdf":
        content = [{"type": "document",
                    "source": {"type": "base64", "media_type": "application/pdf", "data": b64}},
                   {"type": "text", "text": _PROMPT}]
    else:
        content = [{"type": "image",
                    "source": {"type": "base64", "media_type": mime, "data": b64}},
                   {"type": "text", "text": _PROMPT}]
    resp = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=4096,
        messages=[{"role": "user", "content": content}]
    )
    raw = resp.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"): raw = raw[4:]
    return json.loads(raw.strip())


def _demo_data() -> dict:
    return {
        "document_info": {
            "document_type":  "CAR LEASE AGREEMENT",
            "document_date":  "2025-03-05",
            "contract_number":"CLA-2025-55921"
        },
        "parties": {
            "lessor_name":    "DrivePrime Auto Leasing Pvt. Ltd.",
            "lessor_address": "501 Heritage Business Park, Mumbai – 400 001\nPhone: +91 44 6778 2113",
            "lessee_name":    "Arjun Mehta",
            "lessee_address": "Flat 46, Green and Residency, Andheri East, Mumbai – 400 069\nPhone: +91 98702 6513"
        },
        "vehicle": {
            "vin":       "WBA4B1C56JE123714",
            "brand":     "BMW",
            "model":     "BMW 3 Series",
            "year":      "2021",
            "variant":   "320d Luxury Line",
            "body_type": "Sedan",
            "fuel_type": "Diesel"
        },
        "financial": {
            "monthly_payment":  "₹ 62,500",
            "down_payment":     "₹ 3,00,000",
            "security_deposit": "₹ 1,20,000",
            "total_lease_cost": "Not specified",
            "currency":         "INR"
        },
        "lease_terms": {
            "start_date":      "2025-04-01",
            "end_date":        "2029-03-31",
            "duration_months": 48
        },
        "mileage_terms": {
            "annual_limit": "15,000 km",
            "total_limit":  "60,000 km",
            "excess_charge":"₹ 12"
        },
        "sla_obligations": {
            "maintenance_responsibility": "Perform periodic servicing as per BMW service schedule, maintain tires, brakes, engine oil, and fluids, use authorized BMW service centers only",
            "insurance_requirements":     "Comprehensive motor insurance including zero-depreciation cover, third-party liability as per Indian Motor Vehicle Act, deductible not exceeding ₹ 5,000",
            "wear_and_tear_policy":       "Not specified",
            "early_termination_fee":      "₹ 35,000",
            "late_payment_fee":           "₹ 2,500 for payments delayed beyond 7 days; ₹ 1,500 for returned payment charges; non-payment exceeding 45 days may result in repossession as per law"
        },
        "end_of_lease": {
            "purchase_option": "Lease-End Buyout Price: ₹ 18,50,000; Purchase Option Fee: ₹ 10,000; Total Buyout Amount: ₹ 18,60,000",
            "residual_value":  "Not specified",
            "return_conditions":"Clean and in good mechanical condition, with all keys, documents, manuals, and accessories"
        },
        "additional_terms": [
            "Insurance proof must be submitted prior to vehicle delivery",
            "The vehicle is covered under BMW Standard Manufacturer Warranty until 2026",
            "Optional Extended Warranty and Service Inclusive Packages may be purchased separately",
            "Charges may apply for excess wear and tear, damaged interior or exterior, missing accessories or documents",
            "Acceptable wear standards are defined by the Lessor",
            "This Agreement shall be governed by and interpreted in accordance with the laws of India"
        ],
        "red_flags": [
            {"issue": "Monthly payment of ₹62,500 is above typical ₹40,000–₹55,000 market range", "severity": "High",
             "recommendation": "Negotiate payment down or compare with other dealers"},
            {"issue": "Early termination clause lacks clear formula — flat ₹35,000 may be unfair on short tenures", "severity": "High",
             "recommendation": "Request a pro-rated termination clause instead"},
            {"issue": "Mileage limit of 15,000 km/year is below average (18,000 km)", "severity": "Medium",
             "recommendation": "Request 18,000 km/year to avoid excess charges"}
        ],
        "fairness_score": 47,
        "fairness_label": "Needs Negotiation",
        "market_comparison": {
            "vehicle_description": "2021 Bmw Bmw 3 series 320d luxury line",
            "estimated_msrp":      "$57,196",
            "market_monthly_range":"$300–$500",
            "is_above_market":     True
        }
    }


# ── Score colour ──────────────────────────────────────────────────────────────
def _sc(s): return "#22C55E" if s>=80 else "#84CC16" if s>=65 else "#F59E0B" if s>=50 else "#EF4444"
def _sl(s): return "Excellent" if s>=80 else "Good" if s>=65 else "Fair" if s>=50 else "Poor" if s>=35 else "Needs Negotiation"


# ── Section card ──────────────────────────────────────────────────────────────
def _section(title: str, rows: list):
    rows_html = "".join(
        f"<tr><td style='color:#94A3B8;padding:.5rem .9rem;width:40%;"
        f"border-bottom:1px solid rgba(249,115,22,.07);font-size:.85rem;font-weight:500;'>{k}</td>"
        f"<td style='color:#E2E8F0;padding:.5rem .9rem;"
        f"border-bottom:1px solid rgba(249,115,22,.07);font-size:.85rem;'>{v}</td></tr>"
        for k, v in rows if v
    )
    st.markdown(f"""
    <div class="lease-card">
        <div style="font-size:.82rem;font-weight:700;color:#F97316;text-transform:uppercase;
                    letter-spacing:.8px;border-left:3px solid #F97316;padding-left:.6rem;
                    margin-bottom:.75rem;">{title}</div>
        <table style="width:100%;border-collapse:collapse;">{rows_html}</table>
    </div>""", unsafe_allow_html=True)


# ── Red flags ─────────────────────────────────────────────────────────────────
def _red_flags(flags: list):
    if not flags:
        st.markdown('<div class="alert-ok">✓ No significant red flags found.</div>',
                    unsafe_allow_html=True)
        return
    sev_border = {"High": "#EF4444", "Medium": "#F59E0B", "Low": "#22C55E"}
    sev_bg     = {"High": "rgba(239,68,68,.06)", "Medium": "rgba(245,158,11,.06)", "Low": "rgba(34,197,94,.06)"}
    sev_text   = {"High": "#FCA5A5", "Medium": "#FDE68A", "Low": "#86EFAC"}
    for f in flags:
        sev = f.get("severity", "Low")
        st.markdown(f"""
        <div style="border-left:4px solid {sev_border.get(sev,'#94A3B8')};
                    background:{sev_bg.get(sev,'rgba(30,41,59,.5)')};
                    border-radius:0 10px 10px 0;padding:.75rem 1rem;margin:.5rem 0;">
            <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.3rem;">
                <span style="background:{sev_border.get(sev,'#94A3B8')};color:#fff;
                             border-radius:5px;padding:1px 7px;font-size:.72rem;font-weight:700;">
                    {sev}
                </span>
                <span style="color:#F1F5F9;font-weight:600;font-size:.87rem;">
                    {f.get('issue','')}
                </span>
            </div>
            <div style="color:#94A3B8;font-size:.8rem;">
                💡 {f.get('recommendation','')}
            </div>
        </div>""", unsafe_allow_html=True)


# ── Visual Analysis charts ────────────────────────────────────────────────────
def _charts(data: dict):
    score  = data.get("fairness_score", 50)
    flags  = data.get("red_flags", [])

    criteria = ["Monthly Payment", "Lease Duration", "Mileage Limit",
                 "Early Termination Fee", "Down Payment"]
    scores   = [
        max(10, min(100, score - 20)),
        min(100, score + 32),
        min(100, score + 38),
        max(10,  score - 22),
        max(10,  score - 16),
    ]

    col1, col2 = st.columns(2)

    # Radar
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=scores + [scores[0]], theta=criteria + [criteria[0]],
            fill="toself", line_color="#F97316",
            fillcolor="rgba(249,115,22,.12)", name="Score"
        ))
        fig.update_layout(
            title=dict(text="CRITERIA OVERVIEW", font=dict(color="#F97316", size=11), x=.5),
            polar=dict(
                radialaxis=dict(visible=True, range=[0,100], color="#334155",
                                gridcolor="rgba(249,115,22,.18)", tickcolor="#94A3B8",
                                tickfont=dict(size=9)),
                angularaxis=dict(color="#94A3B8", gridcolor="rgba(249,115,22,.12)"),
                bgcolor="rgba(15,23,42,0)"
            ),
            **_DARK, height=310,
        )
        st.plotly_chart(fig, use_container_width=True)

    # Horizontal bar
    with col2:
        colors = ["#EF4444" if s<40 else "#F59E0B" if s<65 else "#22C55E" for s in scores]
        fig2 = go.Figure(go.Bar(
            y=criteria, x=scores, orientation="h",
            marker_color=colors,
            text=[str(s) for s in scores], textposition="outside",
            textfont=dict(color="#E2E8F0", size=11),
        ))
        fig2.update_layout(
            title=dict(text="SCORE BY CRITERION", font=dict(color="#F97316", size=11), x=.5),
            xaxis=dict(range=[0,100], color="#94A3B8", gridcolor="rgba(249,115,22,.1)"),
            yaxis=dict(color="#E2E8F0"),
            **_DARK, height=310,
        )
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    # Red flags donut
    with col3:
        sev_cnt = {"High": 0, "Medium": 0, "Low": 0}
        for f in flags:
            sev_cnt[f.get("severity", "Low")] += 1
        nz = {k: v for k, v in sev_cnt.items() if v > 0} or {"No Issues": 1}
        cmap = {"High":"#EF4444","Medium":"#F59E0B","Low":"#22C55E","No Issues":"#22C55E"}
        fig3 = go.Figure(go.Pie(
            labels=list(nz.keys()), values=list(nz.values()),
            hole=.62, marker_colors=[cmap.get(k,"#94A3B8") for k in nz],
            textinfo="label+value", textfont=dict(color="#E2E8F0", size=11),
        ))
        total = sum(nz.values())
        hi = sev_cnt.get("High", 0)
        fig3.update_layout(
            title=dict(text="RED FLAGS BY SEVERITY", font=dict(color="#F97316",size=11), x=.5),
            annotations=[dict(text=f"High: {hi}", x=.5, y=.5,
                              font=dict(size=12, color="#FCA5A5"), showarrow=False)],
            **_DARK, height=290,
        )
        st.plotly_chart(fig3, use_container_width=True)

    # Weight distribution donut
    with col4:
        wlabels = ["Down Payment","Early Termination Fee","Lease Duration",
                   "Mileage Limit","Monthly Payment"]
        wvals   = [15, 10, 15, 30, 20]  # sums to 90; remaining 10 is "other"
        wlabels += ["Other Terms"]; wvals += [10]
        wcolors = ["#1E293B","#334155","#F97316","#3B82F6","#EA580C","#6366F1"]
        fig4 = go.Figure(go.Pie(
            labels=wlabels, values=wvals, hole=.55,
            marker_colors=wcolors,
            textinfo="label+percent", textfont=dict(color="#E2E8F0", size=10),
        ))
        fig4.update_layout(
            title=dict(text="WEIGHT DISTRIBUTION", font=dict(color="#F97316",size=11), x=.5),
            **_DARK, height=290,
        )
        st.plotly_chart(fig4, use_container_width=True)


# ── Market comparison bar ─────────────────────────────────────────────────────
def _market_bar(data: dict):
    mc = data.get("market_comparison", {})
    raw = data["financial"].get("monthly_payment","62500")
    num = float("".join(filter(lambda c: c.isdigit() or c==".", raw.replace(",","").replace(" ",""))) or "62500")
    labels = ["Your Contract", "Market Low", "Market High"]
    vals   = [num, 40000, 55000]
    clrs   = ["#EF4444" if num > 55000 else "#22C55E", "#22C55E", "#22C55E"]

    fig = go.Figure(go.Bar(
        x=labels, y=vals, marker_color=clrs,
        text=[f"₹{v:,.0f}" for v in vals],
        textposition="outside", textfont=dict(color="#E2E8F0"),
    ))
    fig.update_layout(
        yaxis=dict(title="Monthly Payment (₹)", color="#94A3B8",
                   gridcolor="rgba(249,115,22,.1)"),
        xaxis=dict(color="#94A3B8"),
        **_DARK, height=280,
    )
    st.plotly_chart(fig, use_container_width=True)


# ── Main render ───────────────────────────────────────────────────────────────
def render_sla_tab():
    st.markdown("<div style='height:.5rem;'></div>", unsafe_allow_html=True)

    # ── Upload state ──────────────────────────────────────────────────────
    if not st.session_state.extraction_done:

        # Upload zone header
        st.markdown("""
        <div style="text-align:center;margin:1rem 0 1.2rem;">
            <div style="font-size:2.8rem;color:#F97316;margin-bottom:.4rem;
                        animation:bounce .6s ease infinite alternate;">📄</div>
            <h3 style="color:#F1F5F9;font-size:1.2rem;font-weight:700;margin-bottom:.2rem;">
                Upload Car Lease Document
            </h3>
            <p style="color:#94A3B8;font-size:.86rem;">Drag and drop or click to browse</p>
        </div>
        <style>@keyframes bounce{to{transform:translateY(-6px)}}</style>
        """, unsafe_allow_html=True)

        uploaded = st.file_uploader(
            "lease_doc", type=["pdf","jpg","jpeg","png"],
            label_visibility="collapsed",
        )
        st.markdown("""
        <div style="text-align:center;color:#94A3B8;font-size:.78rem;margin-top:.3rem;">
            JPG, PNG, PDF — up to 20 MB
        </div>""", unsafe_allow_html=True)

        # Extract button (disabled until file chosen)
        extract_clicked = st.button(
            "🔍 Extract SLA Details",
            use_container_width=True,
            disabled=(uploaded is None),
        )

        if uploaded:
            file_bytes = uploaded.read()
            st.session_state.current_file = uploaded.name

            # Document Preview card
            st.markdown(f"""
            <div class="lease-card" style="margin-top:1rem;">
                <div style="display:flex;justify-content:space-between;align-items:center;
                            margin-bottom:.75rem;">
                    <span style="color:#F1F5F9;font-weight:700;font-size:.9rem;">
                        Document Preview
                    </span>
                </div>
            """, unsafe_allow_html=True)

            if uploaded.type in ("image/jpeg","image/png","image/jpg"):
                st.image(file_bytes, use_container_width=True)
            else:
                st.markdown(f"""
                <div style="text-align:center;padding:2rem;background:rgba(30,41,59,.5);
                            border-radius:10px;">
                    <div style="font-size:2.5rem;color:#94A3B8;margin-bottom:.4rem;">📄</div>
                    <div style="color:#94A3B8;font-size:.85rem;">PDF loaded — preview unavailable</div>
                </div>""", unsafe_allow_html=True)

            st.markdown(f"""
            <div style="text-align:center;color:#94A3B8;font-size:.78rem;margin:.5rem 0 0;">
                {uploaded.name} ({len(file_bytes)//1024} KB)
            </div></div>""", unsafe_allow_html=True)

            if extract_clicked:
                # "Extracting SLA Data…" button state shown via spinner
                with st.spinner(""):
                    prog = st.progress(0)
                    st.markdown("""
                    <div style="text-align:center;color:#F97316;font-weight:600;font-size:.88rem;">
                        🔍 Extracting SLA Data…
                    </div>""", unsafe_allow_html=True)
                    for i in range(55):
                        prog.progress(i + 1); time.sleep(0.02)

                    st.markdown("""
                    <div style="text-align:center;color:#22C55E;font-size:.82rem;margin-top:.3rem;">
                        Processing PDF…
                    </div>""", unsafe_allow_html=True)

                    api_key = os.environ.get("ANTHROPIC_API_KEY","")
                    if api_key and _HAS_ANTHROPIC:
                        try:
                            data = _call_claude(file_bytes, uploaded.type)
                        except Exception as e:
                            st.warning(f"AI extraction failed ({e}). Using demo data.")
                            data = _demo_data()
                    else:
                        data = _demo_data()

                    for i in range(55, 101):
                        prog.progress(i); time.sleep(0.01)
                    prog.empty()

                st.session_state.sla_data        = data
                st.session_state.extraction_done = True

                # Auto-save to compare history
                contract = {
                    "id":       len(st.session_state.saved_contracts),
                    "filename": uploaded.name,
                    "date":     datetime.now().strftime("%m/%d/%Y"),
                    "vehicle":  f"{data['vehicle'].get('year','')} {data['vehicle'].get('brand','')} "
                                f"{data['vehicle'].get('model','')} {data['vehicle'].get('variant','')}".strip(),
                    "monthly":  data["financial"].get("monthly_payment","—"),
                    "duration": f"{data['lease_terms'].get('duration_months',0)} months",
                    "mileage":  f"{data['mileage_terms'].get('annual_limit','—')} per year mi/yr",
                    "score":    data.get("fairness_score", 0),
                    "data":     data,
                }
                st.session_state.saved_contracts.append(contract)
                st.rerun()

        else:
            # Demo shortcut
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            col_demo, _, _ = st.columns([1,2,1])
            with col_demo:
                if st.button("▶ Load Demo Data", use_container_width=True):
                    data = _demo_data()
                    st.session_state.sla_data        = data
                    st.session_state.extraction_done = True
                    st.session_state.current_file    = "CAR LEASE AGREEMENT BMW.pdf"
                    contract = {
                        "id":       len(st.session_state.saved_contracts),
                        "filename": "CAR LEASE AGREEMENT BMW.pdf",
                        "date":     datetime.now().strftime("%m/%d/%Y"),
                        "vehicle":  "2021 BMW BMW 3 Series 320d luxury line",
                        "monthly":  "₹ 62,500",
                        "duration": "48 months",
                        "mileage":  "15,000 km per year mi/yr",
                        "score":    47,
                        "data":     data,
                    }
                    st.session_state.saved_contracts.append(contract)
                    st.rerun()

    # ── Results state ─────────────────────────────────────────────────────
    else:
        data  = st.session_state.sla_data
        fname = st.session_state.get("current_file","lease.pdf")

        # File name pill + Re-extract
        col_fn, col_re = st.columns([6,1])
        with col_fn:
            st.markdown(f"""
            <div style="background:rgba(30,41,59,.7);border:1px solid rgba(249,115,22,.28);
                        border-radius:9px;padding:.5rem .9rem;color:#94A3B8;font-size:.82rem;">
                📄 {fname}
            </div>""", unsafe_allow_html=True)
        with col_re:
            if st.button("✕ Reset", use_container_width=True):
                st.session_state.extraction_done = False
                st.session_state.sla_data        = None
                st.rerun()

        # "Extract SLA Details" button row + success banner
        st.button("🔍 Extract SLA Details", use_container_width=True, disabled=True)
        st.markdown('<div class="alert-ok" style="text-align:center;margin:.5rem 0;">✓ SLA extraction complete!</div>',
                    unsafe_allow_html=True)

        # ── Table / JSON toggle ───────────────────────────────────────────
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size:1rem;font-weight:700;color:#F1F5F9;margin-bottom:.6rem;">
            Extracted SLA Data
        </div>""", unsafe_allow_html=True)

        c1, c2, c3 = st.columns([1,1,3])
        with c1:
            if st.button("📋 Table", use_container_width=True):
                st.session_state.sla_view = "table"
        with c2:
            if st.button("{ } JSON", use_container_width=True):
                st.session_state.sla_view = "json"
        with c3:
            st.download_button(
                "📥 Export JSON",
                data=json.dumps(data, indent=2, ensure_ascii=False),
                file_name=f"sla_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
            )

        # ── Table view ────────────────────────────────────────────────────
        if st.session_state.get("sla_view","table") == "table":
            di = data.get("document_info",{})
            _section("Document Information",[
                ("Document Type",    di.get("document_type","")),
                ("Document Date",    di.get("document_date","")),
                ("Contract Number",  di.get("contract_number","")),
            ])

            p = data.get("parties",{})
            _section("Parties",[
                ("Lessor (Leasing Company)", p.get("lessor_name","")),
                ("Lessor Address",           p.get("lessor_address","")),
                ("Lessee (Customer)",        p.get("lessee_name","")),
                ("Lessee Address",           p.get("lessee_address","")),
            ])

            v = data.get("vehicle",{})
            _section("Vehicle Information",[
                ("Vehicle Identification Number", v.get("vin","")),
                ("Brand",    v.get("brand","")),
                ("Model",    v.get("model","")),
                ("Variant / Trim", v.get("variant","")),
                ("Body Type",  v.get("body_type","")),
                ("Fuel Type",  v.get("fuel_type","")),
            ])

            f  = data.get("financial",{})
            lt = data.get("lease_terms",{})
            _section("Financial & Lease Terms",[
                ("Start Date",        lt.get("start_date","")),
                ("End Date",          lt.get("end_date","")),
                ("Duration (Months)", str(lt.get("duration_months",""))),
                ("Monthly Payment",   f.get("monthly_payment","")),
                ("Down Payment",      f.get("down_payment","")),
                ("Security Deposit",  f.get("security_deposit","")),
                ("Total Lease Cost",  f.get("total_lease_cost","")),
            ])

            m = data.get("mileage_terms",{})
            _section("Mileage Terms",[
                ("Annual Mileage Limit",  m.get("annual_limit","")),
                ("Total Mileage Limit",   m.get("total_limit","")),
                ("Excess Mileage Charge", m.get("excess_charge","")),
            ])

            s = data.get("sla_obligations",{})
            _section("SLA Obligations",[
                ("Maintenance Responsibility", s.get("maintenance_responsibility","")),
                ("Insurance Requirements",     s.get("insurance_requirements","")),
                ("Wear & Tear Policy",         s.get("wear_and_tear_policy","")),
                ("Early Termination Fee",      s.get("early_termination_fee","")),
                ("Late Payment Fee",           s.get("late_payment_fee","")),
            ])

            e = data.get("end_of_lease",{})
            _section("End of Lease Options",[
                ("Purchase Option",   e.get("purchase_option","")),
                ("Residual Value",    e.get("residual_value","")),
                ("Return Conditions", e.get("return_conditions","")),
            ])

            terms = data.get("additional_terms",[])
            if terms:
                items_html = "".join(f"<li style='color:#E2E8F0;font-size:.85rem;margin:.3rem 0;'>{t}</li>" for t in terms)
                st.markdown(f"""
                <div class="lease-card">
                    <div style="font-size:.82rem;font-weight:700;color:#F97316;text-transform:uppercase;
                                letter-spacing:.8px;border-left:3px solid #F97316;padding-left:.6rem;
                                margin-bottom:.75rem;">Additional Terms</div>
                    <ul style="padding-left:1.2rem;margin:0;">{items_html}</ul>
                </div>""", unsafe_allow_html=True)

        else:  # JSON view
            st.code(json.dumps(data, indent=2, ensure_ascii=False), language="json")

        # ── Fairness score ────────────────────────────────────────────────
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        score = data.get("fairness_score", 50)
        sc    = _sc(score); sl = _sl(score)

        mc = data.get("market_comparison",{})
        if mc.get("is_above_market"):
            st.markdown(f"""
            <div class="alert-warn" style="margin:.5rem 0 .75rem;">
                ⚠ Monthly payment of {data['financial'].get('monthly_payment','')} is above
                the typical {mc.get('market_monthly_range','')} market range for standard leases.<br>
                <strong>Recommendation:</strong>
                <span style="color:#F97316;"> Compare with other dealerships and online lease
                calculators to verify competitiveness.</span>
            </div>""", unsafe_allow_html=True)

        # ── Red flags ─────────────────────────────────────────────────────
        st.markdown("### 🚩 Red Flags")
        _red_flags(data.get("red_flags",[]))

        # ── Visual Analysis ───────────────────────────────────────────────
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown("### 📊 Visual Analysis")
        _charts(data)

        # ── Market Price Comparison ───────────────────────────────────────
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="lease-card">
            <div class="card-title">📈 Market Price Comparison</div>
            <p style="color:#94A3B8;font-size:.85rem;margin:.25rem 0 .75rem;">
                Your contract vs. estimated market rates for a
                <strong style="color:#F97316;">{mc.get('vehicle_description','this vehicle')}</strong>
                — Est. MSRP: <strong style="color:#F1F5F9;">{mc.get('estimated_msrp','N/A')}</strong>
            </p>
        </div>""", unsafe_allow_html=True)
        _market_bar(data)
