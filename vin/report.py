"""
vin/report.py  —  Tab 2: VIN Report Viewer
Exactly matches video:
  • Large VIN text input placeholder: ENTER 17-CHARACTER VIN (E.G. 1HGCM82633A123456)
  • Character counter "0/17" → turns orange at "17/17"
  • "Get Report" orange button
  • Results: Basic Info card + Technical Specs card
  • Recall History with green/red badge
  • Full History Report section with Carfax link
"""

import streamlit as st
import os

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

_NHTSA_DECODE  = "https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/{}?format=json"
_NHTSA_RECALLS = "https://api.nhtsa.gov/recalls/recallsByVehicle?make={}&model={}&modelYear={}"


def _decode_vin(vin: str) -> dict:
    url = _NHTSA_DECODE.format(vin.upper())
    r   = requests.get(url, timeout=10); r.raise_for_status()
    wanted = {
        "Make":"make","Model":"model","Model Year":"year",
        "Vehicle Type":"vehicle_type","Body Class":"body_class",
        "Fuel Type - Primary":"fuel_type",
        "Manufacturer Name":"manufacturer","Plant Country":"plant_country",
        "Series":"series","Trim":"trim",
        "Engine Number of Cylinders":"cylinders",
        "Displacement (L)":"displacement",
        "Drive Type":"drive_type","Number of Seats":"seats","Doors":"doors",
    }
    info = {}
    for item in r.json().get("Results",[]):
        key = wanted.get(item.get("Variable",""))
        val = item.get("Value","")
        if key and val and val not in ("","null","Not Applicable","0","N/A"):
            info[key] = val
    return info


def _recalls(make: str, model: str, year: str) -> list:
    url = _NHTSA_RECALLS.format(make, model, year)
    r   = requests.get(url, timeout=10); r.raise_for_status()
    return r.json().get("results",[])


def _demo_vin() -> tuple:
    info = {
        "make":"BMW","model":"3 Series","year":"2021",
        "vehicle_type":"PASSENGER CAR","body_class":"Sedan/Saloon",
        "fuel_type":"Diesel","manufacturer":"BMW MANUFACTURER CO., LLC",
        "plant_country":"GERMANY","series":"320d","trim":"Luxury Line",
        "cylinders":"4","displacement":"2.0","drive_type":"RWD",
        "seats":"5","doors":"4",
    }
    return info, []


def render_vin_tab():
    st.markdown("<div style='height:.5rem;'></div>", unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-bottom:1.4rem;">
        <h3 style="color:#F1F5F9;font-size:1.2rem;font-weight:700;margin-bottom:.2rem;">
            🔍 VIN Report Viewer
        </h3>
        <p style="color:#94A3B8;font-size:.85rem;">Look up vehicle details and recall history.</p>
    </div>""", unsafe_allow_html=True)

    # Pre-fill from extracted lease if available
    prefill = ""
    if st.session_state.get("sla_data"):
        prefill = st.session_state.sla_data.get("vehicle",{}).get("vin","")

    col_in, col_btn = st.columns([5, 1])
    with col_in:
        vin = st.text_input(
            "VIN",
            value=prefill,
            placeholder="ENTER 17-CHARACTER VIN (E.G. 1HGCM82633A123456)",
            max_chars=17,
            label_visibility="collapsed",
        )

    with col_btn:
        get = st.button("Get Report", use_container_width=True)

    # Character counter — orange when full
    n   = len(vin.strip())
    clr = "#F97316" if n == 17 else "#94A3B8"
    st.markdown(f"""
    <div style="text-align:right;font-family:'JetBrains Mono',monospace;
                font-size:.8rem;color:{clr};font-weight:{'700' if n==17 else '400'};
                margin-top:-.6rem;">
        {n}/17
    </div>""", unsafe_allow_html=True)

    if get:
        raw = vin.strip()
        if len(raw) < 5:
            st.markdown('<div class="alert-warn">⚠ Please enter a VIN (minimum 5 characters).</div>',
                        unsafe_allow_html=True)
            return

        with st.spinner("Fetching vehicle data…"):
            try:
                if _HAS_REQUESTS:
                    info = _decode_vin(raw)
                    rec  = []
                    if info.get("make") and info.get("model") and info.get("year"):
                        try:
                            rec = _recalls(info["make"], info["model"], info["year"])
                        except Exception:
                            rec = []
                    if not info:
                        info, rec = _demo_vin()
                else:
                    info, rec = _demo_vin()
            except Exception as e:
                st.markdown(f'<div class="alert-warn">⚠ API unavailable ({e}). Showing demo data.</div>',
                            unsafe_allow_html=True)
                info, rec = _demo_vin()

        st.session_state.vin_info    = info
        st.session_state.vin_recalls = rec
        st.session_state.vin_queried = raw.upper()

    # ── Display results ───────────────────────────────────────────────────
    if st.session_state.get("vin_info"):
        info    = st.session_state.vin_info
        rec     = st.session_state.vin_recalls or []
        queried = st.session_state.vin_queried

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

        # Vehicle title card
        vname = f"{info.get('year','')} {info.get('make','')} {info.get('model','')} {info.get('series','')}".strip()
        st.markdown(f"""
        <div class="lease-card" style="display:flex;align-items:center;gap:1rem;padding:1.1rem 1.3rem;">
            <div style="font-size:2.2rem;">🚗</div>
            <div>
                <div style="font-size:1.1rem;font-weight:800;color:#F1F5F9;">{vname}</div>
                <div style="color:#F97316;font-family:'JetBrains Mono',monospace;font-size:.8rem;margin-top:2px;">
                    VIN: {queried}
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        def _info_card(title, rows):
            rows_html = "".join(
                f"<tr>"
                f"<td style='color:#94A3B8;padding:.45rem .8rem;width:46%;font-size:.83rem;"
                f"border-bottom:1px solid rgba(249,115,22,.07);font-weight:500;'>{k}</td>"
                f"<td style='color:#E2E8F0;padding:.45rem .8rem;font-size:.83rem;"
                f"border-bottom:1px solid rgba(249,115,22,.07);'>{v}</td></tr>"
                for k, v in rows if v and v != "—"
            )
            return f"""
            <div class="lease-card">
                <div class="card-title">{title}</div>
                <table style="width:100%;border-collapse:collapse;">{rows_html}</table>
            </div>"""

        with col1:
            st.markdown(_info_card("Basic Information",[
                ("Make",         info.get("make","—")),
                ("Model",        info.get("model","—")),
                ("Year",         info.get("year","—")),
                ("Series / Trim",f"{info.get('series','')} {info.get('trim','')}".strip() or "—"),
                ("Body Class",   info.get("body_class","—")),
                ("Drive Type",   info.get("drive_type","—")),
            ]), unsafe_allow_html=True)

        with col2:
            st.markdown(_info_card("Technical Specifications",[
                ("Fuel Type",        info.get("fuel_type","—")),
                ("Engine (L)",       info.get("displacement","—")),
                ("Cylinders",        info.get("cylinders","—")),
                ("Seats",            info.get("seats","—")),
                ("Doors",            info.get("doors","—")),
                ("Manufacturer Name",info.get("manufacturer","—")),
                ("Vehicle Type",     info.get("vehicle_type","—")),
                ("Plant Country",    info.get("plant_country","—")),
            ]), unsafe_allow_html=True)

        # Recall History
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        n_rec = len(rec)
        badge_bg  = "#22C55E" if n_rec == 0 else "#EF4444"
        badge_txt = f"{n_rec} recall{'s' if n_rec!=1 else ''}"

        st.markdown(f"""
        <div class="lease-card">
            <div style="display:flex;align-items:center;gap:.6rem;margin-bottom:.6rem;">
                <div class="card-title" style="margin-bottom:0;">Recall History</div>
                <span style="background:{badge_bg};color:#fff;border-radius:12px;
                             padding:1px 9px;font-size:.72rem;font-weight:700;">
                    {badge_txt}
                </span>
            </div>
        """, unsafe_allow_html=True)

        if n_rec == 0:
            st.markdown('<div style="color:#22C55E;font-weight:600;font-size:.88rem;padding:.3rem 0;">✓ No recalls found for this vehicle.</div>',
                        unsafe_allow_html=True)
        else:
            for item in rec[:10]:
                st.markdown(f"""
                <div style="border-left:3px solid #EF4444;padding:.5rem .75rem;margin:.4rem 0;
                            background:rgba(239,68,68,.05);border-radius:0 8px 8px 0;">
                    <div style="color:#FCA5A5;font-weight:600;font-size:.83rem;">
                        {item.get('Component','Unknown Component')}
                    </div>
                    <div style="color:#94A3B8;font-size:.78rem;margin-top:2px;">
                        {item.get('Summary',item.get('Consequence','No description available'))[:220]}
                    </div>
                </div>""", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Full History Report
        st.markdown("""
        <div class="lease-card">
            <div class="card-title">Full History Report</div>
            <p style="color:#94A3B8;font-size:.84rem;margin-bottom:.9rem;">
                Accident history and odometer data require a paid report.
            </p>
        </div>""", unsafe_allow_html=True)

        c1, c2, _ = st.columns([1,1,2])
        with c1:
            st.link_button("View Carfax Report (Paid)",
                           f"https://www.carfax.com/VehicleHistory/p/Report.cfx?vin={queried}",
                           use_container_width=True)
        with c2:
            st.link_button("AutoCheck Report",
                           f"https://www.autocheck.com/vehiclehistory/?vin={queried}",
                           use_container_width=True)
