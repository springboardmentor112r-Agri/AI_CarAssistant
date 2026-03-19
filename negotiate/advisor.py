"""
negotiate/advisor.py  —  Tab 3: Negotiate
Exactly matches video:
  • Empty state: orange chat icon, "Lease Negotiation Advisor" heading,
    subtext, "Your loaded lease data is available as context." (conditional)
  • 5 quick-action chip buttons in 2 rows
  • Text input: "Ask about lease terms, negotiation tactics…"
  • Orange send ➤ button
  • Chat: user bubble (right, orange), bot bubble (left, dark card)
  • Clear conversation link
"""

import streamlit as st
import os
import json

try:
    import anthropic
    _HAS_ANTHROPIC = True
except ImportError:
    _HAS_ANTHROPIC = False

_CHIPS = [
    "What lease terms are typically negotiable?",
    "Explain my monthly payment and what affects it",
    "How can I reduce excess mileage penalties?",
    "What should I watch out for before signing?",
    "Help me understand my end-of-lease options",
]


def _system_prompt(sla_data) -> str:
    base = (
        "You are an expert lease negotiation advisor with 15 years of experience in auto leasing. "
        "Help customers understand lease clauses, identify negotiable terms, and craft effective "
        "counter-offers. Be concise and practical. Use bullet points for key points. "
        "Highlight important numbers and terms. End with a concrete action the user can take."
    )
    if sla_data:
        ctx = json.dumps({
            "vehicle":       sla_data.get("vehicle",{}),
            "financial":     sla_data.get("financial",{}),
            "lease_terms":   sla_data.get("lease_terms",{}),
            "mileage_terms": sla_data.get("mileage_terms",{}),
            "sla_obligations":sla_data.get("sla_obligations",{}),
            "red_flags":     sla_data.get("red_flags",[]),
            "fairness_score":sla_data.get("fairness_score",0),
        }, indent=2)
        base += f"\n\nThe user has loaded the following lease contract data:\n{ctx}"
    return base


def _call_claude(messages: list, sla_data) -> str:
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY",""))
    resp   = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=1024,
        system=_system_prompt(sla_data),
        messages=messages,
    )
    return resp.content[0].text


def _mock(user_msg: str, sla_data) -> str:
    if sla_data:
        mp = sla_data.get("financial",{}).get("monthly_payment","₹ 62,500")
        return (
            f"Given your current monthly payment is **{mp}**, propose a lower amount based on "
            f"your budget. For example, you could say: \"Considering my budget, I would prefer "
            f"a monthly payment of ₹ 60,000. Can we adjust the terms to accommodate this?\"\n\n"
            "**Key points:**\n"
            f"- Current monthly payment: {mp}\n"
            "- Proposed monthly payment: ₹ 60,000\n\n"
            "**Additional considerations:**\n"
            "- Mention your financial situation.\n"
            "- Be prepared to discuss other terms if the dealer counters.\n\n"
            "---\n*Add your `ANTHROPIC_API_KEY` to `.env` for live AI responses.*"
        )
    return (
        "I can help you negotiate your lease! Please upload your lease document in the "
        "**Extract SLA** tab first so I can give you personalised advice.\n\n"
        "In general, the most negotiable lease terms are:\n"
        "- **Monthly payment** — always try to negotiate this down\n"
        "- **Mileage allowance** — request higher limits upfront\n"
        "- **Money factor** — the lease equivalent of an interest rate\n"
        "- **Down payment** — lower is usually better in a lease\n\n"
        "---\n*Add your `ANTHROPIC_API_KEY` to `.env` for live AI responses.*"
    )


def _get_response(user_msg: str, sla_data):
    api_key = os.environ.get("ANTHROPIC_API_KEY","")
    msgs    = [{"role": m["role"], "content": m["content"]}
               for m in st.session_state.chat_history]
    if api_key and _HAS_ANTHROPIC:
        try:
            return _call_claude(msgs, sla_data)
        except Exception as e:
            return f"Error: {e}\n\n{_mock(user_msg, sla_data)}"
    return _mock(user_msg, sla_data)


def _send(msg: str, sla_data):
    st.session_state.chat_history.append({"role":"user","content":msg})
    reply = _get_response(msg, sla_data)
    st.session_state.chat_history.append({"role":"assistant","content":reply})


def render_negotiate_tab():
    st.markdown("<div style='height:.5rem;'></div>", unsafe_allow_html=True)

    sla_data = st.session_state.get("sla_data")
    history  = st.session_state.get("chat_history",[])

    # ── Empty state ───────────────────────────────────────────────────────
    if not history:
        context_note = (
            "<br><span style='color:#F97316;font-weight:600;'>"
            "Your loaded lease data is available as context.</span>"
            if sla_data else ""
        )
        st.markdown(f"""
        <div style="text-align:center;padding:2.5rem 1rem 1.5rem;">
            <div style="width:64px;height:64px;
                        background:linear-gradient(135deg,#F97316,#EA580C);
                        border-radius:50%;margin:0 auto .9rem;
                        display:flex;align-items:center;justify-content:center;
                        font-size:1.8rem;box-shadow:0 0 20px rgba(249,115,22,.35);">
                💬
            </div>
            <h3 style="color:#F1F5F9;font-size:1.15rem;font-weight:700;margin-bottom:.4rem;">
                Lease Negotiation Advisor
            </h3>
            <p style="color:#94A3B8;font-size:.86rem;max-width:460px;margin:0 auto;line-height:1.55;">
                I can help you understand lease clauses, spot what's negotiable,
                and craft better counter-offers.{context_note}
            </p>
        </div>""", unsafe_allow_html=True)

        # Quick prompt chips — 3 on row 1, 2 on row 2
        row1 = st.columns(3)
        row2 = st.columns(2)
        for i, chip in enumerate(_CHIPS):
            col = row1[i] if i < 3 else row2[i - 3]
            with col:
                if st.button(chip, key=f"chip_{i}", use_container_width=True):
                    _send(chip, sla_data)
                    st.rerun()
    else:
        # ── Chat history ──────────────────────────────────────────────────
        for msg in history:
            if msg["role"] == "user":
                st.markdown(f"""
                <div style="display:flex;justify-content:flex-end;margin-bottom:.6rem;gap:.4rem;">
                    <div class="chat-user">{msg['content']}</div>
                    <div style="width:30px;height:30px;background:linear-gradient(135deg,#F97316,#EA580C);
                                border-radius:50%;flex-shrink:0;display:flex;align-items:center;
                                justify-content:center;font-size:.85rem;margin-top:2px;">👤</div>
                </div>""", unsafe_allow_html=True)
            else:
                # Render markdown-ish content safely
                content = msg['content'].replace("**Key points:**","<strong>Key points:</strong>")
                content = content.replace("**Additional considerations:**","<strong>Additional considerations:</strong>")
                # Inline bold
                import re
                content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
                # Bullet points
                content = re.sub(r'(?m)^- (.+)$', r'• \1', content)
                content = content.replace('\n', '<br>')
                st.markdown(f"""
                <div style="display:flex;gap:.5rem;margin-bottom:.6rem;align-items:flex-start;">
                    <div style="width:30px;height:30px;background:linear-gradient(135deg,#F97316,#EA580C);
                                border-radius:50%;flex-shrink:0;display:flex;align-items:center;
                                justify-content:center;font-size:.85rem;margin-top:2px;">💬</div>
                    <div class="chat-bot">{content}</div>
                </div>""", unsafe_allow_html=True)

    # ── Input bar ─────────────────────────────────────────────────────────
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    col_inp, col_send = st.columns([11, 1])
    with col_inp:
        user_input = st.text_input(
            "msg",
            placeholder="Ask about lease terms, negotiation tactics…",
            label_visibility="collapsed",
            key="chat_input_field",
        )
    with col_send:
        send_btn = st.button("➤", use_container_width=True, key="send_btn")

    val = st.session_state.get("chat_input_field","").strip()
    if (send_btn and val) or (val and st.session_state.get("_last_input") != val and
                               len(st.session_state.chat_history) > 0 and
                               st.session_state.chat_history[-1]["content"] != val):
        pass  # handled below via form

    if send_btn and val:
        _send(val, sla_data)
        st.rerun()

    if history:
        if st.button("🗑 Clear conversation", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()
