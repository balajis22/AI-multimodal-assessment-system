from html import escape
from pathlib import Path

import streamlit as st

try:
    from .firebase_auth import (
        FirebaseAuthError,
        get_user_profile,
        login_user,
        register_user,
        send_password_reset_email,
        send_verification_email,
    )
except ImportError:
    from auth.firebase_auth import (
        FirebaseAuthError,
        get_user_profile,
        login_user,
        register_user,
        send_password_reset_email,
        send_verification_email,
    )


def load_auth_css():
    css_path = Path(__file__).resolve().parent / "style.css"

    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )


def _establish_session(result, profile=None):
    uid = result["localId"]
    if profile is None:
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
    st.session_state.pop("auth_account_not_found_email", None)
    st.session_state.pop("auth_registration_mode", None)
    st.session_state.pop("auth_forgot_password_mode", None)
    st.session_state.pop("auth_prefill_email", None)
    st.session_state.pop("auth_verification_notice", None)
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

    if "auth_verification_notice" in st.session_state:
        st.success(st.session_state.pop("auth_verification_notice"))

    with st.form("firebase_login_form", clear_on_submit=False):
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
        col_forgot, col_signup = st.columns(2)
        with col_forgot:
            forgot_submitted = st.form_submit_button(
                "Forgot password?",
                type="secondary",
                use_container_width=True,
            )
        with col_signup:
            signup_submitted = st.form_submit_button(
                "Sign up",
                type="secondary",
                use_container_width=True,
            )

    if signup_submitted:
        st.session_state["auth_prefill_email"] = email.strip()
        st.session_state["auth_registration_mode"] = True
        st.session_state.pop("auth_forgot_password_mode", None)
        st.rerun()

    if forgot_submitted:
        st.session_state["auth_prefill_email"] = email.strip()
        st.session_state["auth_forgot_password_mode"] = True
        st.session_state.pop("auth_registration_mode", None)
        st.rerun()

    if submitted:
        email = email.strip()
        if not email or not password:
            st.error("Please enter your email and password.")
            return

        try:
            with st.spinner("Signing in..."):
                result = login_user(email, password)
                profile = get_user_profile(result["idToken"], result["localId"])
        except FirebaseAuthError as exc:
            st.session_state["auth_prefill_email"] = email
            if exc.code == "EMAIL_NOT_FOUND":
                st.session_state["auth_account_not_found_email"] = email
            else:
                st.session_state.pop("auth_account_not_found_email", None)
                st.error(str(exc))
        else:
            is_verified = (
                profile.get("emailVerified") is True
                or str(profile.get("emailVerified", "")).lower() == "true"
            )
            if not is_verified:
                st.session_state["auth_prefill_email"] = email
                try:
                    send_verification_email(result["idToken"])
                    st.warning(
                        f"Your email address (**{email}**) is not verified yet. "
                        "A fresh verification link has been sent to your inbox. "
                        "Please check your email and verify your account before signing in."
                    )
                except FirebaseAuthError as exc:
                    st.warning(
                        f"Your email address (**{email}**) is not verified yet. "
                        "Please check your email and verify your account before signing in. "
                        f"(Could not send verification email: {exc})"
                    )
                return

            try:
                _establish_session(result, profile=profile)
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
                    send_verification_email(result["idToken"])
            except FirebaseAuthError as exc:
                st.error(str(exc))
            else:
                st.session_state["auth_prefill_email"] = email
                st.session_state["auth_registration_mode"] = False
                st.session_state["auth_verification_notice"] = (
                    f"Account created successfully for **{email}**! "
                    "A verification link has been sent to your email. "
                    "Please check your inbox (and spam folder) and verify your email before signing in."
                )
                st.rerun()

    if st.button("Back to Sign In", key="auth_back_to_login"):
        st.session_state.pop("auth_registration_mode", None)
        st.session_state.pop("auth_forgot_password_mode", None)
        st.rerun()


def _render_forgot_password():
    st.markdown(
        """
        <div class="login-brand">
            <span class="login-brand-mark">A</span>
            <span>AI Multimodal Assessment System</span>
        </div>
        <div class="login-intro">
            <div class="login-eyebrow">ACCOUNT RECOVERY</div>
            <h1>Reset your password</h1>
            <p>Enter your email address to receive a password reset link.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("firebase_forgot_password_form", clear_on_submit=False):
        email = st.text_input(
            "Email",
            placeholder="you@example.com",
            value=st.session_state.get("auth_prefill_email", ""),
            key="auth_forgot_email",
        )
        submitted = st.form_submit_button(
            "Send Reset Link",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        email = email.strip()
        if not email:
            st.error("Please enter your email address.")
        else:
            try:
                with st.spinner("Sending password reset email..."):
                    send_password_reset_email(email)
            except FirebaseAuthError as exc:
                st.error(str(exc))
            else:
                st.session_state["auth_prefill_email"] = email
                st.session_state.pop("auth_forgot_password_mode", None)
                st.session_state["auth_verification_notice"] = (
                    f"Password reset link sent to **{email}**! "
                    "Please check your inbox (and spam folder) to set a new password."
                )
                st.rerun()

    if st.button("Back to Sign In", key="auth_forgot_back_to_login", use_container_width=True):
        st.session_state.pop("auth_forgot_password_mode", None)
        st.rerun()


def render_auth():
    load_auth_css()
    with st.container(key="auth-screen"):
        if st.session_state.get("auth_registration_mode"):
            _render_registration()
        elif st.session_state.get("auth_forgot_password_mode"):
            _render_forgot_password()
        else:
            _render_login()


def logout_user():
    for key in (
        "auth_user",
        "auth_id_token",
        "auth_refresh_token",
        "auth_account_not_found_email",
        "auth_registration_mode",
        "auth_forgot_password_mode",
        "auth_forgot_email",
        "auth_prefill_email",
        "auth_verification_notice",
        "auth_login_email",
        "auth_login_password",
        "auth_registration_name",
        "auth_registration_email",
        "auth_registration_password",
        "auth_registration_confirm_password",
        "candidate_profile_uid",
        "candidate_profile",
        "candidate_profile_photo",
        "candidate_photo_url",
        "auth_mfa_enabled",
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


def render_authenticated_controls():
    user = st.session_state["auth_user"]
    display_name = escape(user.get("name") or user.get("email") or "user")
    email = escape(user.get("email") or "")
    current_page = st.session_state.get("current_page", "home")

    identity, settings_col = st.columns([6, 1.4])
    with identity:
        st.caption(f"Signed in as **{display_name}** ({email})")

    with settings_col:
        if current_page == "settings":
            if st.button("🏠 Lobby", key="top_nav_home", use_container_width=True):
                st.session_state.current_page = "home"
                st.rerun()
        else:
            if st.button("⚙️ Settings", key="top_nav_settings", use_container_width=True):
                st.session_state.current_page = "settings"
                st.rerun()
