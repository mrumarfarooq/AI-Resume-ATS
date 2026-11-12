import streamlit as st
import sys
from pathlib import Path

# Make project root available for imports.
sys.path.insert(0, str(Path(__file__).parent.parent))

st.set_page_config(
    page_title="ResumeATS",
    page_icon=":material/description:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state.
for key, default in [
    ("access_token", None),
    ("refresh_token", None),
    ("user_id", None),
    ("user_email", None),
    ("auth_error", None),
    ("auth_info", None),
    ("current_view", "landing"),
    ("public_menu_open", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default


from frontend.services import supabase_client
from frontend.views import landing, scorer, history, resources, auth

# Handle email verification callback.
if "token_hash" in st.query_params:
    token_hash = st.query_params.get("token_hash")
    token_type = st.query_params.get("type", "email")

    st.query_params.clear()

    st.session_state["auth_mode"] = "signin"
    st.session_state.current_view = "auth"

    if token_type != "email":
        st.session_state.auth_error = (
            "Invalid email verification link."
        )
    else:
        result = supabase_client.verify_signup_email_token(
            token_hash
        )

        if "error" in result:
            st.session_state.auth_error = (
                f"Email verification failed: {result['error']}"
            )
        else:
            st.session_state.auth_info = (
                "Email verified successfully! "
                "Your account is ready. Please sign in to continue."
            )

    st.rerun()

# Handle Google OAuth and password recovery callbacks.
if not st.session_state.access_token and "code" in st.query_params:
    is_recovery = (
        st.query_params.get("auth_flow") == "recovery"
    )

    auth_code = st.query_params["code"]

    result = supabase_client.exchange_code_for_session(auth_code)

    st.query_params.clear()

    if "error" in result:
        if is_recovery:
            st.session_state.auth_error = (
                f"Password recovery failed: {result['error']}"
            )
        else:
            st.session_state.auth_error = (
                f"Google sign-in failed: {result['error']}"
            )

        st.session_state.current_view = "auth"

    else:
        st.session_state.access_token = result["access_token"]
        st.session_state.refresh_token = result["refresh_token"]
        st.session_state.user_id = result["user_id"]
        st.session_state.user_email = result["email"]

        if is_recovery:
            st.session_state["auth_mode"] = "update_password"
            st.session_state.current_view = "auth"
        else:
            st.session_state.current_view = "scorer"

    st.rerun()

# Open the Forgot Password page when requested.
if st.query_params.get("auth_mode") == "forgot_password":
    st.session_state.current_view = "auth"


# Load custom CSS.
def load_css():
    css_path = Path(__file__).parent / "assets" / "styles.css"

    try:
        with open(css_path, "r", encoding="utf-8") as file:
            return f"<style>{file.read()}</style>"
    except FileNotFoundError:
        return ""


st.markdown(load_css(), unsafe_allow_html=True)


# Public navigation.
if not st.session_state.access_token and st.session_state.current_view != "auth":

    # Desktop navbar.
    with st.container(key="public-navbar-desktop"):
        nav1, nav2, nav3, nav4 = st.columns([3, 1, 1, 1])

        with nav1:
            st.markdown(
                """
                <div class="brand-logo">
                    <span class="brand-icon">
                        <svg viewBox="0 0 24 24" width="23" height="23"
                             fill="none" stroke="currentColor" stroke-width="1.8"
                             stroke-linecap="round" stroke-linejoin="round">
                            <path d="M6 3h8l5 5v13H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"/>
                            <path d="M14 3v5h5"/>
                            <path d="m8 15 2.5 2.5L16 12"/>
                        </svg>
                    </span>
                    <span>Resume<span class="brand-highlight">ATS</span></span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with nav2:
            if st.button("Home", use_container_width=True, key="public_home_button"):
                st.session_state.current_view = "landing"
                st.rerun()

        with nav3:
            if st.button("Features", use_container_width=True, key="public_features_button"):
                st.session_state.current_view = "landing"
                st.session_state.scroll_to_features = True
                st.session_state.scroll_request_id = (
                    st.session_state.get("scroll_request_id", 0) + 1
                )
                st.rerun()

        with nav4:
            if st.button("Sign in", use_container_width=True, key="public_signin_button"):
                st.session_state.current_view = "auth"
                st.rerun()

    # Mobile navbar.
    with st.container(key="public-navbar-mobile"):
        mobile_logo, mobile_toggle = st.columns([5, 1])

        with mobile_logo:
            st.markdown(
                """
                <div class="brand-logo">
                    <span class="brand-icon">
                        <svg viewBox="0 0 24 24" width="23" height="23"
                             fill="none" stroke="currentColor" stroke-width="1.8"
                             stroke-linecap="round" stroke-linejoin="round">
                            <path d="M6 3h8l5 5v13H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"/>
                            <path d="M14 3v5h5"/>
                            <path d="m8 15 2.5 2.5L16 12"/>
                        </svg>
                    </span>
                    <span>Resume<span class="brand-highlight">ATS</span></span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with mobile_toggle:
            menu_label = "✕" if st.session_state.public_menu_open else "☰"

            if st.button(
                menu_label,
                use_container_width=True,
                key="responsive_menu_toggle",
            ):
                st.session_state.public_menu_open = (
                    not st.session_state.public_menu_open
                )
                st.rerun()

    # Mobile dropdown menu.
    if st.session_state.public_menu_open:
        with st.container(key="public-mobile-menu"):

            if st.button("Home", use_container_width=True, key="mob_nav_home"):
                st.session_state.public_menu_open = False
                st.session_state.current_view = "landing"
                st.rerun()

            if st.button("Features", use_container_width=True, key="mob_nav_features"):
                st.session_state.public_menu_open = False
                st.session_state.current_view = "landing"
                st.session_state.scroll_to_features = True
                st.session_state.scroll_request_id = (
                    st.session_state.get("scroll_request_id", 0) + 1
                )
                st.rerun()

            if st.button("Sign in", use_container_width=True, key="mob_nav_signin"):
                st.session_state.public_menu_open = False
                st.session_state.current_view = "auth"
                st.rerun()


# Dashboard sidebar for signed-in users.
if st.session_state.access_token:
    with st.sidebar:
        st.markdown(
            """
<div class="brand-logo">
    <span class="brand-icon">
        <svg viewBox="0 0 24 24" width="23" height="23"
             fill="none" stroke="currentColor" stroke-width="1.8"
             stroke-linecap="round" stroke-linejoin="round">
            <path d="M6 3h8l5 5v13H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"/>
            <path d="M14 3v5h5"/>
            <path d="m8 15 2.5 2.5L16 12"/>
        </svg>
    </span>
    <span>Resume<span class="brand-highlight">ATS</span></span>
</div>
            """,
            unsafe_allow_html=True,
        )

        st.caption("Dashboard Navigation")
        st.markdown("---")

        if st.button(
            "Resume Analyzer",
            use_container_width=True,
            type="primary" if st.session_state.current_view == "scorer" else "secondary",
            key="nav_resume_analyzer",
        ):
            st.session_state.current_view = "scorer"
            st.rerun()

        if st.button(
            "History",
            use_container_width=True,
            type="primary" if st.session_state.current_view == "history" else "secondary",
            key="nav_history",
        ):
            st.session_state.current_view = "history"
            st.rerun()

        if st.button(
            "Resources",
            use_container_width=True,
            type="primary" if st.session_state.current_view == "resources" else "secondary",
            key="nav_resources",
        ):
            st.session_state.current_view = "resources"
            st.rerun()

        st.markdown("---")
        st.markdown("### Account")
        st.caption(f"Signed in as {st.session_state.user_email}")

        if st.button(
            "Sign out",
            use_container_width=True,
            key="sidebar_signout_button",
        ):
            supabase_client.sign_out()

            # Clear authentication data.
            for key in (
                "access_token",
                "refresh_token",
                "user_id",
                "user_email",
            ):
                st.session_state[key] = None

            # Clear uploaded files and analysis data.
            for key in (
                "resume_upload",
                        "scorer_pdf_bytes",
                "scorer_analysis",
                "download_pdf_report",
                "download_summary",
                "analysis_mode",
                "selected_job_role",
                "custom_job_role",
            ):
                st.session_state.pop(key, None)

            st.session_state.current_view = "landing"
            st.rerun()


# Protect dashboard pages.
protected_views = {"scorer", "history", "resources"}

if (
    st.session_state.current_view in protected_views
    and not st.session_state.access_token
):
    st.session_state.current_view = "auth"
    st.session_state.auth_info = (
        "Please sign in or create an account to access your dashboard."
    )
    st.rerun()


# Render selected page.
current_view = st.session_state.current_view

if current_view == "landing":
    landing.render()

elif current_view == "auth":
    auth.render()

elif current_view == "scorer":
    scorer.render()

elif current_view == "history":
    history.render()

elif current_view == "resources":
    resources.render()
