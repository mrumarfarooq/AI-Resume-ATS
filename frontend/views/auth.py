import re
from html import escape
import streamlit as st
from frontend.services import supabase_client


def _set_authenticated_user(result: dict) -> None:
    st.session_state["access_token"] = result["access_token"]
    st.session_state["refresh_token"] = result["refresh_token"]
    st.session_state["user_id"] = result["user_id"]
    st.session_state["user_email"] = result["email"]


def _valid_email(value: str) -> bool:
    return bool(
        re.fullmatch(
            r"[^\s@]+@[^\s@]+\.[^\s@]+",
            value.strip(),
        )
    )


def render() -> None:
    if "auth_mode" not in st.session_state:
        st.session_state["auth_mode"] = "signin"

    if st.query_params.get("auth_mode") == "forgot_password":
        st.session_state["auth_mode"] = "forgot_password"

    is_signup = st.session_state["auth_mode"] == "signup"
    is_forgot_password = (
        st.session_state["auth_mode"] == "forgot_password"
    )
    is_update_password = (
        st.session_state["auth_mode"] == "update_password"
    )

    st.markdown(
        '<div class="auth-viewport-spacer"></div>',
        unsafe_allow_html=True,
    )

    _, center, _ = st.columns([1, 1.15, 1])

    with center:
        if is_update_password:
            heading = "Create a new password."
            description = "Choose a strong password for your account."

        elif is_forgot_password:
            heading = "Reset your password."
            description = "Enter your email to receive a password reset link."

        elif is_signup:
            heading = "Create your account."
            description = "Get started with smarter resume analysis."

        else:
            heading = "Welcome back."
            description = "Sign in to continue to your ResumeATS account."

        st.markdown(
            '<div class="auth-card-heading">'
            '<div class="auth-brand-symbol">'
            '<svg viewBox="0 0 24 24" aria-hidden="true">'
            '<path d="M6 3h8l5 5v13H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"/>'
            '<path d="M14 3v5h5"/>'
            '<path d="m8 15 2.5 2.5L16 12"/>'
            '</svg></div>'
            '<div class="saas-kicker">RESUMEATS ACCOUNT</div>'
            f'<h1>{heading}</h1>'
            f'<p>{description}</p>'
            '</div>',
            unsafe_allow_html=True,
        )

        if st.session_state.get("auth_error"):
            st.error(st.session_state["auth_error"])
            st.session_state["auth_error"] = None

        if st.session_state.get("auth_info"):
            st.info(st.session_state["auth_info"])
            st.session_state["auth_info"] = None

        # UPDATE PASSWORD PAGE
        if is_update_password:
            with st.form("update_password_form"):
                new_password = st.text_input(
                    "New password",
                    type="password",
                    placeholder="At least 8 characters",
                )

                confirm_password = st.text_input(
                    "Confirm new password",
                    type="password",
                    placeholder="Re-enter your new password",
                )

                update_submitted = st.form_submit_button(
                    "Update password",
                    use_container_width=True,
                    type="primary",
                )

            if update_submitted:
                if len(new_password) < 8:
                    st.session_state.auth_error = (
                        "Use a password with at least 8 characters."
                    )
                    st.rerun()

                if new_password != confirm_password:
                    st.session_state.auth_error = (
                        "Passwords do not match."
                    )
                    st.rerun()

                result = supabase_client.update_user_password(
                    new_password
                )

                if "error" in result:
                    st.session_state.auth_error = result["error"]
                else:
                    supabase_client.sign_out()

                    for key in (
                        "access_token",
                        "refresh_token",
                        "user_id",
                        "user_email",
                    ):
                        st.session_state[key] = None

                    st.session_state["auth_mode"] = "signin"
                    st.session_state.auth_info = (
                        "Password updated successfully. Please sign in "
                        "with your new password."
                    )

                st.rerun()
        elif is_forgot_password:
            with st.form("forgot_password_form"):
                reset_email = st.text_input(
                    "Email address",
                    key="reset_email",
                    placeholder="name@example.com",
                )

                reset_submitted = st.form_submit_button(
                    "Send reset link",
                    use_container_width=True,
                    type="primary",
                )

            if reset_submitted:
                if not _valid_email(reset_email):
                    st.session_state.auth_error = (
                        "Enter a valid email address."
                    )
                    st.rerun()

                result = supabase_client.send_password_reset_email(
                    reset_email.strip()
                )

                if "error" in result:
                    st.session_state.auth_error = result["error"]
                else:
                    st.session_state.auth_info = (
                        "If an account exists with this email, "
                        "a password reset link will be sent."
                    )

                st.rerun()

            if st.button(
                "Back to sign in",
                key="forgot_back_to_signin",
                type="tertiary",
            ):
                st.session_state["auth_mode"] = "signin"
                st.query_params.pop("auth_mode", None)
                st.rerun()

        elif is_signup:
            with st.container(key="signup-card"):

                with st.form("signup_form", clear_on_submit=False):
                    email = st.text_input(
                        "Email address",
                        key="signup_email",
                        placeholder="name@example.com",
                    )

                    password = st.text_input(
                        "Create password",
                        type="password",
                        key="signup_pw",
                        placeholder="At least 8 characters",
                    )

                    submitted = st.form_submit_button(
                        "Create account",
                        use_container_width=True,
                        type="primary",
                    )

                if submitted:
                    if not _valid_email(email):
                        st.session_state.auth_error = (
                            "Enter a valid email address."
                        )
                        st.rerun()

                    if len(password) < 8:
                        st.session_state.auth_error = (
                            "Use a password with at least 8 characters."
                        )
                        st.rerun()

                    result = supabase_client.sign_up_with_password(
                        email.strip(), password
                    )

                    if "error" in result:
                        st.session_state.auth_error = result["error"]

                    elif result.get("pending_confirmation"):
                        st.session_state.auth_info = (
                            f"Account created. Confirm your email using the "
                            f"link sent to {result['email']} before signing in."
                        )

                    else:
                        _set_authenticated_user(result)
                        st.session_state.auth_info = "Your account is ready."
                        st.session_state.current_view = "scorer"

                    st.rerun()

                # SIGNUP PAGE TOGGLE
                if st.button(
                    "Already have an account? Sign in",
                    key="auth_switch_to_signin",
                    type="tertiary",
                ):
                    st.session_state["auth_mode"] = "signin"
                    st.query_params.pop("auth_mode", None)
                    st.rerun()

        # SIGNIN PAGE
        else:
            with st.container(key="signin-card"):

                with st.form("signin_form", clear_on_submit=False):
                    email = st.text_input(
                        "Email address",
                        key="signin_email",
                        placeholder="name@example.com",
                    )

                    password = st.text_input(
                        "Password",
                        type="password",
                        key="signin_pw",
                        placeholder="Enter your password",
                    )

                    st.markdown(
                        '<div class="forgot-password-link">'
                        '<a href="?auth_mode=forgot_password">'
                        'Forgot password?</a>'
                        '</div>',
                        unsafe_allow_html=True,
                    )

                    submitted = st.form_submit_button(
                        "Sign in",
                        use_container_width=True,
                        type="primary",
                    )

                if submitted:
                    if not _valid_email(email):
                        st.session_state.auth_error = (
                            "Enter a valid email address."
                        )
                        st.rerun()

                    if not password:
                        st.session_state.auth_error = (
                            "Enter your password."
                        )
                        st.rerun()

                    result = supabase_client.sign_in_with_password(
                        email.strip(), password
                    )

                    if "error" in result:
                        st.session_state.auth_error = result["error"]

                    else:
                        _set_authenticated_user(result)
                        st.session_state.current_view = "scorer"

                    st.rerun()

                # SIGNIN PAGE TOGGLE
                if st.button(
                    "New to ResumeATS? Create an account",
                    key="auth_switch_to_signup",
                    type="tertiary",
                ):
                    st.session_state["auth_mode"] = "signup"
                    st.rerun()

        # GOOGLE OAUTH
        if not is_update_password and not is_forgot_password:
            st.markdown(
                '<div class="auth-or"><span>OR CONTINUE WITH</span></div>',
                unsafe_allow_html=True,
            )

            oauth = supabase_client.google_oauth_url()

            if "error" in oauth:
                st.caption(
                    "Google sign-in is currently unavailable. "
                    "Check the Supabase OAuth configuration."
                )
            else:
                google_url = escape(oauth["url"], quote=True)

                st.markdown(
                    f'''
                    <a class="google-oauth-button" href="{google_url}">
                        <svg viewBox="0 0 48 48" aria-hidden="true">
                            <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5Z"/>
                            <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.76 7.18l7.73 6C44.42 37.97 46.98 31.87 46.98 24.55Z"/>
                            <path fill="#FBBC05" d="M10.53 28.59A14.4 14.4 0 0 1 9.75 24c0-1.59.27-3.13.76-4.59l-7.98-6.19A23.9 23.9 0 0 0 0 24c0 3.87.93 7.52 2.56 10.78l7.97-6.19Z"/>
                            <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.91-5.8l-7.73-6c-2.14 1.45-4.89 2.3-8.18 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48Z"/>
                        </svg>
                        <span>Continue with Google</span>
                    </a>
                    ''',
                    unsafe_allow_html=True,
                )

            st.markdown(
                '<p class="auth-small-note">'
                'ResumeATS analyzes your resume to generate useful feedback and improvement suggestions.'
                '</p>',
                unsafe_allow_html=True,
            )

            if st.button(
                "Back to home",
                key="auth_back_home",
                use_container_width=True,
                type="tertiary",
            ):
                st.session_state.current_view = "landing"
                st.rerun()
