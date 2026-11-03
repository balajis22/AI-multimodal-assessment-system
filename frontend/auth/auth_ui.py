from html import escape
from pathlib import Path

import streamlit as st

try:
    from .firebase_auth import (
        FirebaseAuthError,
        get_user_profile,
        login_user,
        register_user,
    )
except ImportError:
    from auth.firebase_auth import (
        FirebaseAuthError,
        get_user_profile,
        login_user,
        register_user,
    )


def load_auth_css():
    css_path = Path(__file__).resolve().parent / "style.css"

    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )


def _establish_session(result):
    uid = result["localId"]
    profile = get_user_profile(result["idToken"], uid)
    same_user = st.session_state.get("candidate_profile_uid") == uid
    name = profile.get("displayName") or (
        st.session_state.get("candidate_name", "") if same_user else ""
    )
    email = profile.get("email") or result["email"]

    st.session_state["auth_user"] = {
        "uid": uid,
        "email": email,
        "name": name,
    }
    st.session_state["auth_id_token"] = result["idToken"]
    st.session_state["auth_refresh_token"] = result["refreshToken"]
    st.session_state["candidate_profile_uid"] = uid
    st.session_state["candidate_profile"] = {
        "uid": uid,
        "name": name,
        "email": email,
    }
    st.session_state["candidate_name"] = name
    st.session_state["candidate_email"] = email
    st.session_state.pop("auth_account_not_found", None)
    st.session_state.pop("auth_registration_mode", None)
    st.session_state.pop("auth_prefill_email", None)
    st.rerun()


def _render_login():
    st.markdown(
        """
        <div class="login-brand">
            <span class="login-brand-mark">A</span>
            <span>AI Multimodal Assessment System</span>
        </div>
        <div class="login-intro">
            <div class="login-eyebrow">WELCOME BACK</div>
            <h1>Sign in to your account</h1>
            <p>Enter your credentials to access the assessment studio.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("firebase_login_form", clear_on_submit=True):
        email = st.text_input(
            "Email",
            placeholder="you@example.com",
            value=st.session_state.get("auth_prefill_email", ""),
            key="auth_login_email",
        )
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            key="auth_login_password",
        )
        submitted = st.form_submit_button(
            "Sign In",
            type="primary",
            use_container_width=True,
        )
        signup_submitted = st.form_submit_button(
            "Sign up",
            type="secondary",
            use_container_width=True,
        )

    st.caption("Don't have an account?")
    if signup_submitted:
        st.session_state["auth_prefill_email"] = email.strip()
        st.session_state["auth_registration_mode"] = True
        st.rerun()

    if submitted:
        email = email.strip()
        if not email or not password:
            st.error("Please enter your email and password.")
            return

        try:
            with st.spinner("Signing in..."):
                result = login_user(email, password)
        except FirebaseAuthError as exc:
            st.session_state["auth_prefill_email"] = email
            if exc.code == "EMAIL_NOT_FOUND":
                st.session_state["auth_account_not_found_email"] = email
            else:
                st.session_state.pop("auth_account_not_found_email", None)
                st.error(str(exc))
        else:
            try:
                _establish_session(result)
            except FirebaseAuthError as exc:
                st.error(str(exc))

    missing_email = st.session_state.get("auth_account_not_found_email", "")
    if missing_email and email.casefold() == missing_email.casefold():
        st.error("No account found. Please create a new account.")
        if st.button("Create New Account", key="auth_create_account"):
            st.session_state["auth_registration_mode"] = True
            st.rerun()


def _render_registration():
    st.markdown(
        """
        <div class="auth-card">
            <h1 class="auth-title">Create New Account</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("firebase_registration_form", clear_on_submit=True):
        name = st.text_input(
            "Full name",
            placeholder="Enter your full name",
            key="auth_registration_name",
        )
        email = st.text_input(
            "Email",
            value=st.session_state.get("auth_prefill_email", ""),
            placeholder="you@example.com",
            key="auth_registration_email",
        )
        password = st.text_input(
            "Password",
            type="password",
            placeholder="At least 6 characters",
            key="auth_registration_password",
        )
        confirm_password = st.text_input(
            "Confirm password",
            type="password",
            placeholder="Re-enter your password",
            key="auth_registration_confirm_password",
        )
        submitted = st.form_submit_button(
            "Create New Account",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        email = email.strip()
        if not name.strip() or not email or not password:
            st.error("Please complete all fields.")
        elif password != confirm_password:
            st.error("Your passwords do not match.")
        elif len(password) < 6:
            st.error("Password must contain at least 6 characters.")
        else:
            try:
                with st.spinner("Creating your account..."):
                    result = register_user(name, email, password)
                    _establish_session(result)
            except FirebaseAuthError as exc:
                st.error(str(exc))

    if st.button("Back to Sign In", key="auth_back_to_login"):
        st.session_state.pop("auth_registration_mode", None)
        st.rerun()


def render_auth():
    load_auth_css()
    with st.container(key="auth-screen"):
        if st.session_state.get("auth_registration_mode"):
            _render_registration()
        else:
            _render_login()


def render_authenticated_controls():
    user = st.session_state["auth_user"]
    display_name = escape(user.get("name") or user.get("email") or "user")
    email = escape(user.get("email") or "")

    identity, logout = st.columns([6, 1])
    with identity:
        st.caption(f"Signed in as **{display_name}** ({email})")

    with logout:
        if st.button("Log out", key="auth_logout", use_container_width=True):
            for key in (
                "auth_user",
                "auth_id_token",
                "auth_refresh_token",
                "auth_account_not_found_email",
                "auth_registration_mode",
                "auth_prefill_email",
                "auth_login_email",
                "auth_login_password",
                "auth_registration_name",
                "auth_registration_email",
                "auth_registration_password",
                "auth_registration_confirm_password",
                "candidate_profile_uid",
                "candidate_profile",
                "current_page",
                "candidate_name",
                "candidate_email",
                "active_role",
                "question_idx",
                "duration",
                "interview_completed",
                "last_result",
            ):
                st.session_state.pop(key, None)
            st.rerun()
