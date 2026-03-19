"""
auth/user_auth.py
Sign In / Sign Up for Car Lease Analyzer.
All user data is persisted in users.db via auth/db.py.
"""

import streamlit as st
import time
from datetime import datetime

from auth.db import init_db, get_user, email_exists, create_user, _hash


# ── Session init ──────────────────────────────────────────────────────────────
def init_auth_session():
    """Call once from main(). Sets up DB and session state defaults."""
    init_db()  # creates users.db + table if not already there
    defaults = {
        "authenticated": False,
        "username":      "",
        "display_name":  "",
        "auth_mode":     "signin",
        "auth_error":    "",
        "auth_success":  "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── Shared CSS ────────────────────────────────────────────────────────────────
_AUTH_CSS = """
<style>
@keyframes carFloat {
    0%,100%{ transform: translateY(0) rotate(-3deg); }
    50%    { transform: translateY(-18px) rotate(3deg); }
}
@keyframes roadMove { to { background-position: 100px 0; } }
</style>
"""

def _car_panel():
    st.markdown("""
    <div style="display:flex;align-items:center;justify-content:center;
                height:100%;min-height:500px;position:relative;">
        <div style="font-size:9rem;animation:carFloat 3s ease-in-out infinite;
                    filter:drop-shadow(0 0 40px rgba(249,115,22,.4));
                    color:#F97316;user-select:none;">🚗</div>
        <div style="position:absolute;bottom:18%;left:0;right:0;height:3px;
                    background:repeating-linear-gradient(90deg,#F97316 0 60px,
                    transparent 60px 100px);opacity:.55;
                    animation:roadMove 1.2s linear infinite;"></div>
    </div>""", unsafe_allow_html=True)

def _card_header(title: str, subtitle: str):
    st.markdown(f"""
    <div style="background:#fff;border-radius:18px;padding:2.4rem 2.2rem 1rem;
                max-width:400px;margin:2rem auto;box-shadow:0 24px 64px rgba(0,0,0,.25);">
        <div style="display:flex;align-items:center;justify-content:center;
                    gap:.55rem;margin-bottom:1.2rem;">
            <div style="width:32px;height:32px;background:linear-gradient(135deg,#F97316,#EA580C);
                        border-radius:8px;display:flex;align-items:center;
                        justify-content:center;font-size:1.1rem;">🚗</div>
            <span style="font-size:1rem;font-weight:700;color:#1E293B;">Car Lease Analyzer</span>
        </div>
        <div style="font-size:1.4rem;font-weight:800;color:#0F172A;text-align:center;
                    margin-bottom:.25rem;">{title}</div>
        <div style="font-size:.85rem;color:#64748B;text-align:center;
                    margin-bottom:1.2rem;">{subtitle}</div>
    </div>""", unsafe_allow_html=True)

def _show_error(msg: str):
    if msg:
        st.markdown(f"""
        <div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;
                    padding:.55rem .9rem;color:#B91C1C;font-size:.83rem;margin-bottom:.8rem;">
            ⚠ {msg}
        </div>""", unsafe_allow_html=True)

def _show_success(msg: str):
    if msg:
        st.markdown(f"""
        <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;
                    padding:.55rem .9rem;color:#15803D;font-size:.83rem;margin-bottom:.8rem;">
            ✓ {msg}
        </div>""", unsafe_allow_html=True)

def _label(text: str):
    st.markdown(f"<span style='font-size:.82rem;font-weight:600;color:#374151;'>{text}</span>",
                unsafe_allow_html=True)


# ── Sign-In page ──────────────────────────────────────────────────────────────
def render_login_page():
    st.markdown(_AUTH_CSS, unsafe_allow_html=True)
    col_left, col_right = st.columns([1.1, 1])

    with col_left:
        _car_panel()

    with col_right:
        _card_header("Welcome back", "Sign in to continue to your workspace")
        _show_error(st.session_state.auth_error)

        with st.form("signin_form", clear_on_submit=False):
            _label("Email")
            email = st.text_input("Email", placeholder="you@example.com",
                                  label_visibility="collapsed")
            _label("Password")
            password = st.text_input("Password", type="password",
                                     placeholder="••••••••",
                                     label_visibility="collapsed")
            submitted = st.form_submit_button("Sign In", use_container_width=True)

        if submitted:
            with st.spinner("Please wait…"):
                time.sleep(0.6)
                _do_signin(email.strip().lower(), password)

        st.markdown("<div style='text-align:center;font-size:.85rem;color:#6B7280;margin-top:.8rem;'>"
                    "Don't have an account?</div>", unsafe_allow_html=True)
        if st.button("Sign up →", key="goto_signup", use_container_width=True):
            st.session_state.auth_mode  = "signup"
            st.session_state.auth_error = ""
            st.rerun()


# ── Sign-Up page ──────────────────────────────────────────────────────────────
def render_signup_page():
    st.markdown(_AUTH_CSS, unsafe_allow_html=True)
    col_left, col_right = st.columns([1.1, 1])

    with col_left:
        _car_panel()

    with col_right:
        _card_header("Create account", "Free forever. No credit card required.")
        _show_error(st.session_state.auth_error)
        _show_success(st.session_state.auth_success)

        with st.form("signup_form", clear_on_submit=False):
            _label("Full Name")
            name = st.text_input("Full Name", placeholder="Your name",
                                 label_visibility="collapsed")
            _label("Email")
            email = st.text_input("Email", placeholder="you@example.com",
                                  label_visibility="collapsed", key="su_email")
            _label("Password")
            pw1 = st.text_input("Password", type="password",
                                placeholder="Min 6 characters",
                                label_visibility="collapsed", key="su_pw1")
            _label("Confirm Password")
            pw2 = st.text_input("Confirm Password", type="password",
                                placeholder="Repeat password",
                                label_visibility="collapsed", key="su_pw2")
            submitted = st.form_submit_button("Create Account", use_container_width=True)

        if submitted:
            with st.spinner("Creating account…"):
                time.sleep(0.5)
                _do_signup(name.strip(), email.strip().lower(), pw1, pw2)

        st.markdown("<div style='text-align:center;font-size:.85rem;color:#6B7280;margin-top:.8rem;'>"
                    "Already have an account?</div>", unsafe_allow_html=True)
        if st.button("← Sign in", key="goto_signin", use_container_width=True):
            st.session_state.auth_mode    = "signin"
            st.session_state.auth_error   = ""
            st.session_state.auth_success = ""
            st.rerun()


# ── Auth logic ────────────────────────────────────────────────────────────────
def _do_signin(email: str, password: str):
    user = get_user(email)
    if user and user["password_hash"] == _hash(password):
        st.session_state.authenticated = True
        st.session_state.username      = email
        st.session_state.display_name  = user["name"]
        st.session_state.auth_error    = ""
        st.rerun()
    else:
        st.session_state.auth_error = "Invalid email or password. Try demo@demo.com / demo123"
        st.rerun()


def _do_signup(name: str, email: str, pw1: str, pw2: str):
    if not name:
        st.session_state.auth_error = "Please enter your full name."
        st.rerun()
        return
    if not email or "@" not in email:
        st.session_state.auth_error = "Please enter a valid email address."
        st.rerun()
        return
    if email_exists(email):
        st.session_state.auth_error = "An account with this email already exists."
        st.rerun()
        return
    if len(pw1) < 6:
        st.session_state.auth_error = "Password must be at least 6 characters."
        st.rerun()
        return
    if pw1 != pw2:
        st.session_state.auth_error = "Passwords do not match."
        st.rerun()
        return

    ok = create_user(
        email=email,
        name=name,
        password_hash=_hash(pw1),
        created_at=datetime.now().strftime("%Y-%m-%d"),
    )
    if not ok:
        st.session_state.auth_error = "An account with this email already exists."
        st.rerun()
        return

    st.session_state.auth_success  = f"Account created! Signing you in as {name}…"
    st.session_state.auth_error    = ""
    time.sleep(0.4)
    st.session_state.authenticated = True
    st.session_state.username      = email
    st.session_state.display_name  = name
    st.rerun()


# ── Router ────────────────────────────────────────────────────────────────────
def render_auth_page():
    if st.session_state.get("auth_mode", "signin") == "signup":
        render_signup_page()
    else:
        render_login_page()


# ── Sidebar profile ───────────────────────────────────────────────────────────
def render_user_profile():
    name  = st.session_state.get("display_name", "User")
    email = st.session_state.get("username", "")

    st.markdown(f"""
    <div style="padding:.5rem .5rem 1rem;text-align:center;">
        <div style="width:44px;height:44px;background:linear-gradient(135deg,#F97316,#EA580C);
                    border-radius:50%;margin:0 auto .5rem;display:flex;align-items:center;
                    justify-content:center;font-size:1.2rem;color:#fff;font-weight:700;">
            {name[0].upper()}
        </div>
        <div style="color:#F1F5F9;font-weight:700;font-size:.95rem;">{name}</div>
        <div style="color:#94A3B8;font-size:.72rem;margin-top:2px;">{email}</div>
    </div>
    <div style="height:1px;background:linear-gradient(90deg,transparent,
                rgba(249,115,22,.4),transparent);margin:.75rem 0;"></div>
    """, unsafe_allow_html=True)

    if st.button("Sign Out", use_container_width=True, key="signout_btn"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


def check_permission(_perm: str = "") -> bool:
    return st.session_state.get("authenticated", False)
