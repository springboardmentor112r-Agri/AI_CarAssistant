"""
compare/contracts.py  —  Tab 4: Compare
Exactly matches video:
  • "Compare Contracts" heading + sub-text
  • Compare (N) button top-right + Clear Selection
  • Contract list with checkboxes, vehicle name, filename/date, monthly/duration/mileage pills,
    and circular score badge (green/amber/red) + label (EXCELLENT/FAIR/POOR…)
  • Side-by-side modal:
      - "Side-by-Side Comparison" dark header
      - Best Deal banner (star + vehicle name + Fairness Score: N/100 label)
      - Score gauge cards per contract with BEST DEAL ribbon
      - Full field comparison table (scrollable, highlighted best column)
      - Fairness score bar chart
"""

import streamlit as st
import plotly.graph_objects as go

_DARK = dict(
    plot_bgcolor  = "rgba(15,23,42,0)",
    paper_bgcolor = "rgba(0,0,0,0)",
    font          = dict(family="Inter", color="#E2E8F0"),
    margin        = dict(l=16, r=16, t=36, b=16),
)

def _sc(s): return "#22C55E" if s>=80 else "#84CC16" if s>=65 else "#F59E0B" if s>=50 else "#EF4444"
def _sl(s): return "Excellent" if s>=80 else "Good" if s>=65 else "Fair" if s>=50 else "Poor" if s>=35 else "Needs Negotiation"
def _n_flags(c): return len(c.get("data",{}).get("red_flags",[]))

_FIELDS = [
    ("Monthly Payment",     lambda d: d.get("financial",{}).get("monthly_payment","—")),
    ("Down Payment",        lambda d: d.get("financial",{}).get("down_payment","—")),
    ("Security Deposit",    lambda d: d.get("financial",{}).get("security_deposit","—")),
    ("Duration",            lambda d: str(d.get("lease_terms",{}).get("duration_months","—"))+" months"),
    ("Total Lease Cost",    lambda d: d.get("financial",{}).get("total_lease_cost","Not specified")),
    ("Annual Mileage Limit",lambda d: d.get("mileage_terms",{}).get("annual_limit","—")),
    ("Excess Mileage Charge",lambda d: d.get("mileage_terms",{}).get("excess_charge","—")),
    ("Security Deposit",    lambda d: d.get("financial",{}).get("security_deposit","—")),
    ("Early Termination Fee",lambda d: d.get("sla_obligations",{}).get("early_termination_fee","—")),
    ("Late Payment Fee",    lambda d: d.get("sla_obligations",{}).get("late_payment_fee","—")),
    ("Residual Value",      lambda d: d.get("end_of_lease",{}).get("residual_value","—")),
    ("Purchase Option",     lambda d: d.get("end_of_lease",{}).get("purchase_option","—")),
    ("Maintenance",         lambda d: d.get("sla_obligations",{}).get("maintenance_responsibility","—")[:80]+"…"),
    ("Fairness Score",      lambda d: f"{d.get('fairness_score','—')}/100"),
]


def render_compare_tab():
    st.markdown("<div style='height:.5rem;'></div>", unsafe_allow_html=True)
    contracts = st.session_state.get("saved_contracts",[])

    if not contracts:
        st.markdown("""
        <div class="lease-card" style="text-align:center;padding:3rem 2rem;">
            <div style="font-size:3.5rem;margin-bottom:.75rem;">📊</div>
            <div style="color:#F97316;font-size:1.1rem;font-weight:700;">No Contracts Yet</div>
            <div style="color:#94A3B8;font-size:.85rem;margin-top:.4rem;">
                Extract lease documents in the <strong>Extract SLA</strong> tab to build your history.
            </div>
        </div>""", unsafe_allow_html=True)
        return

    selection = st.session_state.get("compare_sel",[])

    # ── Header row ────────────────────────────────────────────────────────
    col_h, col_btns = st.columns([3,1])
    with col_h:
        st.markdown("""
        <div>
            <h3 style="color:#F1F5F9;font-size:1.2rem;font-weight:700;margin-bottom:.2rem;">
                Compare Contracts
            </h3>
            <p style="color:#94A3B8;font-size:.83rem;">
                Select contracts from your history to compare side-by-side and find the best deal.
            </p>
        </div>""", unsafe_allow_html=True)

    with col_btns:
        n_sel = len(selection)
        do_cmp = st.button(
            f"📊 Compare ({n_sel})" if n_sel else "📊 Compare",
            use_container_width=True,
            disabled=(n_sel < 2),
        )
        if st.button("Clear Selection", use_container_width=True):
            st.session_state.compare_sel  = []
            st.session_state.show_compare = False
            st.rerun()

    if do_cmp:
        st.session_state.show_compare = True

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # ── Contract list ─────────────────────────────────────────────────────
    for c in contracts:
        cid      = c["id"]
        score    = c.get("score",0)
        sc       = _sc(score); sl = _sl(score)
        selected = cid in selection
        nf       = _n_flags(c)

        chk_col, info_col, score_col = st.columns([0.45, 7, 1.3])

        with chk_col:
            checked = st.checkbox("", value=selected, key=f"ck_{cid}",
                                  label_visibility="collapsed")
            if checked and cid not in selection:
                selection.append(cid)
                st.session_state.compare_sel = selection
            elif not checked and cid in selection:
                selection.remove(cid)
                st.session_state.compare_sel = selection

        with info_col:
            border = "#F97316" if selected else "rgba(249,115,22,.2)"
            bg     = "rgba(249,115,22,.07)" if selected else "rgba(30,41,59,.7)"
            flag_pill = (
                f"<span style='background:rgba(239,68,68,.12);color:#FCA5A5;"
                f"border-radius:20px;padding:1px 9px;font-size:.72rem;'>"
                f"⚠ {nf} red flag{'s' if nf!=1 else ''}</span>"
            ) if nf > 0 else ""
            st.markdown(f"""
            <div style="background:{bg};border:1.5px solid {border};border-radius:12px;
                        padding:.9rem 1.1rem;transition:all .18s;">
                <div style="font-size:.92rem;font-weight:700;color:#F1F5F9;margin-bottom:3px;">
                    {c.get('vehicle','Unknown')}
                </div>
                <div style="color:#64748B;font-size:.76rem;margin-bottom:6px;">
                    {c.get('filename','')} &nbsp;•&nbsp; {c.get('date','')}
                </div>
                <div style="display:flex;gap:.6rem;flex-wrap:wrap;align-items:center;">
                    <span style="background:rgba(249,115,22,.12);color:#FED7AA;
                                 border:1px solid rgba(249,115,22,.3);border-radius:20px;
                                 padding:1px 9px;font-size:.73rem;font-weight:600;">
                        {c.get('monthly','—')}/mo
                    </span>
                    <span style="background:rgba(30,41,59,.9);color:#94A3B8;
                                 border-radius:20px;padding:1px 9px;font-size:.73rem;">
                        {c.get('duration','—')}
                    </span>
                    <span style="background:rgba(30,41,59,.9);color:#94A3B8;
                                 border-radius:20px;padding:1px 9px;font-size:.73rem;">
                        {c.get('mileage','—')}
                    </span>
                    {flag_pill}
                </div>
            </div>""", unsafe_allow_html=True)

        with score_col:
            st.markdown(f"""
            <div style="text-align:center;padding:.7rem .5rem;background:rgba(30,41,59,.8);
                        border:1px solid rgba(249,115,22,.2);border-radius:11px;margin-top:2px;">
                <div style="font-size:1.6rem;font-weight:900;color:{sc};
                            font-family:'JetBrains Mono',monospace;">{score}</div>
                <div style="font-size:.62rem;color:{sc};font-weight:700;
                            text-transform:uppercase;letter-spacing:.4px;">{sl}</div>
            </div>""", unsafe_allow_html=True)

    # ── Side-by-side panel ────────────────────────────────────────────────
    if st.session_state.get("show_compare") and len(selection) >= 2:
        sel_contracts = [c for c in contracts if c["id"] in selection]
        best = max(sel_contracts, key=lambda c: c.get("score",0))

        st.markdown("<div class='divider' style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)

        # Close button
        if st.button("✕ Close comparison", key="close_cmp"):
            st.session_state.show_compare = False
            st.rerun()

        # Dark panel header
        st.markdown("""
        <div style="background:rgba(15,23,42,.95);border:1px solid rgba(249,115,22,.3);
                    border-radius:14px 14px 0 0;padding:1rem 1.4rem;
                    font-size:1rem;font-weight:800;color:#F1F5F9;">
            Side-by-Side Comparison
        </div>""", unsafe_allow_html=True)

        # Best deal banner
        bs = best.get("score",0)
        st.markdown(f"""
        <div style="background:rgba(249,115,22,.1);border:1px solid rgba(249,115,22,.3);
                    border-left:none;border-right:none;
                    padding:.65rem 1.4rem;display:flex;align-items:center;gap:.6rem;">
            <span style="font-size:1.1rem;">⭐</span>
            <span style="color:#FED7AA;font-weight:700;font-size:.88rem;">
                Best Deal: {best.get('vehicle','—')} —
                <span style="color:{_sc(bs)};">
                    Fairness Score: {bs}/100 ({_sl(bs)})
                </span>
            </span>
        </div>""", unsafe_allow_html=True)

        # Score gauge cards
        gcols = st.columns(len(sel_contracts))
        for i, c in enumerate(sel_contracts):
            with gcols[i]:
                is_best = c["id"] == best["id"]
                s = c.get("score",0); sc2=_sc(s); sl2=_sl(s)
                nf = _n_flags(c)
                ribbon = (
                    '<div style="position:absolute;top:-10px;left:50%;'
                    'transform:translateX(-50%);background:#F97316;color:#fff;'
                    'font-size:.62rem;font-weight:800;padding:2px 9px;'
                    'border-radius:9px;letter-spacing:.8px;white-space:nowrap;">BEST DEAL</div>'
                ) if is_best else ""
                st.markdown(f"""
                <div style="background:{'rgba(249,115,22,.07)' if is_best else 'rgba(30,41,59,.75)'};
                            border:2px solid {'#F97316' if is_best else 'rgba(249,115,22,.2)'};
                            border-radius:12px;padding:1rem .75rem;text-align:center;
                            position:relative;margin-top:.75rem;
                            {'box-shadow:0 0 18px rgba(249,115,22,.18);' if is_best else ''}">
                    {ribbon}
                    <div style="font-size:.78rem;font-weight:700;color:#F1F5F9;
                                margin:{'1rem' if is_best else '0'} 0 .4rem;line-height:1.3;">
                        {c.get('vehicle','')[:28]}
                    </div>
                    <div style="font-size:2.2rem;font-weight:900;color:{sc2};
                                font-family:'JetBrains Mono',monospace;">{s}</div>
                    <div style="font-size:.65rem;color:#94A3B8;margin-bottom:.3rem;">/100</div>
                    <div style="background:rgba(0,0,0,.3);color:{sc2};font-weight:700;
                                font-size:.72rem;border-radius:18px;padding:2px 10px;
                                display:inline-block;margin-bottom:.4rem;">{sl2}</div><br>
                    <span style="background:rgba(239,68,68,.12);color:#FCA5A5;
                                 font-size:.67rem;border-radius:12px;padding:1px 7px;">
                        ⚠ {nf} red flag{'s' if nf!=1 else ''}
                    </span>
                </div>""", unsafe_allow_html=True)

        # Field comparison table
        st.markdown("<div style='height:.75rem;'></div>", unsafe_allow_html=True)

        # Table header
        hcols = st.columns([1.8] + [2]*len(sel_contracts))
        with hcols[0]:
            st.markdown("<span style='color:#F97316;font-size:.78rem;font-weight:700;'>FIELD</span>",
                        unsafe_allow_html=True)
        for i, c in enumerate(sel_contracts):
            with hcols[i+1]:
                short = c.get("vehicle","")[:22] + ("…" if len(c.get("vehicle",""))>22 else "")
                st.markdown(f"<span style='color:#F97316;font-size:.75rem;font-weight:700;'>{short}</span>",
                            unsafe_allow_html=True)

        seen = set()
        for fname, extractor in _FIELDS:
            if fname in seen: continue
            seen.add(fname)
            rcols = st.columns([1.8] + [2]*len(sel_contracts))
            with rcols[0]:
                st.markdown(f"""
                <div style="color:#94A3B8;font-size:.8rem;padding:.42rem 0;
                            border-bottom:1px solid rgba(249,115,22,.07);">{fname}</div>""",
                            unsafe_allow_html=True)
            for i, c in enumerate(sel_contracts):
                val = extractor(c.get("data",{}))
                is_best_col = c["id"] == best["id"]
                with rcols[i+1]:
                    st.markdown(f"""
                    <div style="color:{'#F97316' if is_best_col else '#E2E8F0'};
                                font-size:.8rem;font-weight:{'700' if is_best_col else '400'};
                                padding:.42rem 0;
                                background:{'rgba(249,115,22,.04)' if is_best_col else 'transparent'};
                                border-bottom:1px solid rgba(249,115,22,.07);">{val}</div>""",
                                unsafe_allow_html=True)

        # Fairness bar chart
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        names  = [c.get("vehicle","")[:20] for c in sel_contracts]
        scores = [c.get("score",0) for c in sel_contracts]
        colors = [_sc(s) for s in scores]

        fig = go.Figure(go.Bar(
            x=names, y=scores, marker_color=colors,
            text=[f"{s}/100" for s in scores],
            textposition="outside", textfont=dict(color="#E2E8F0",size=11),
        ))
        fig.update_layout(
            title=dict(text="Fairness Score Comparison",
                       font=dict(color="#F97316",size=12), x=.5),
            yaxis=dict(range=[0,100], color="#94A3B8",
                       gridcolor="rgba(249,115,22,.1)", title="Score"),
            xaxis=dict(color="#94A3B8"),
            **_DARK, height=300,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)
