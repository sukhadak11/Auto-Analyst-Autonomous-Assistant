import streamlit as st

from services.auth_service import (
    login_user,
    register_user,
)

from components.sidebar import show_sidebar

from views.dashboard import show_dashboard
from views.new_analysis import show_new_analysis
from views.jobs import show_jobs
from views.reports import show_reports
from views.profile import show_profile
from views.admin_dashboard import show_admin_dashboard
from views.job_details import show_job_details


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AutoAnalyst",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

.stApp {
    background-color: #f7f8fc;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1400px;
}

section[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e6e8ef;
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 2rem;
}

.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    min-height: 42px;
}

[data-testid="stFileUploader"] {
    background-color: #ffffff;
    border-radius: 10px;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "access_token" not in st.session_state:
    st.session_state.access_token = None

if "user_email" not in st.session_state:
    st.session_state.user_email = ""

if "user_id" not in st.session_state:
    st.session_state.user_id = ""

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

if "user_role" not in st.session_state:
    st.session_state.user_role = "user"

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

if "selected_job" not in st.session_state:
    st.session_state.selected_job = None


# ============================================================
# LOGIN / REGISTER
# ============================================================

def show_login():

    st.markdown(
        """
        <div style="text-align:center; margin-top:3rem;">
            <h1 style="font-size:2.2rem; margin-bottom:0.3rem;">
                AutoAnalyst
            </h1>
            <p style="color:#6b7280;">
                Autonomous data analysis and insights
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    login_tab, register_tab = st.tabs(
        ["Login", "Create Account"]
    )

    # ========================================================
    # LOGIN
    # ========================================================

    with login_tab:

        with st.container(border=True):

            st.subheader("Welcome back")

            st.caption(
                "Sign in to access your analyses and reports."
            )

            email = st.text_input(
                "Email",
                placeholder="you@example.com",
                key="login_email",
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password",
            )

            st.write("")

            if st.button(
                "Sign In",
                type="primary",
                use_container_width=True,
                key="login_button",
            ):

                if not email.strip():

                    st.warning(
                        "Please enter your email."
                    )

                elif not password:

                    st.warning(
                        "Please enter your password."
                    )

                else:

                    data, error = login_user(
                        email.strip(),
                        password,
                    )

                    if error:

                        st.error(error)

                    else:

                        # ------------------------------------
                        # Authentication
                        # ------------------------------------

                        st.session_state.authenticated = True

                        st.session_state.access_token = (
                            data["access_token"]
                        )

                        st.session_state.user_email = (
                            data["email"]
                        )

                        st.session_state.user_id = (
                            data["user_id"]
                        )

                        # ------------------------------------
                        # Admin role
                        # ------------------------------------

                        st.session_state.is_admin = bool(
                            data.get("is_admin", False)
                        )

                        if st.session_state.is_admin:
                            st.session_state.user_role = "admin"
                        else:
                            st.session_state.user_role = "user"

                        # ------------------------------------
                        # Default page
                        # ------------------------------------

                        st.session_state.page = "Dashboard"
                        st.session_state.selected_job = None

                        st.rerun()

    # ========================================================
    # REGISTER
    # ========================================================

    with register_tab:

        with st.container(border=True):

            st.subheader(
                "Create your account"
            )

            st.caption(
                "Start analyzing your datasets with AutoAnalyst."
            )

            email = st.text_input(
                "Email",
                placeholder="you@example.com",
                key="register_email",
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Create a password",
                key="register_password",
            )

            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Re-enter your password",
                key="register_confirm_password",
            )

            st.write("")

            if st.button(
                "Create Account",
                type="primary",
                use_container_width=True,
                key="register_button",
            ):

                if not email.strip():

                    st.warning(
                        "Please enter your email."
                    )

                elif not password:

                    st.warning(
                        "Please create a password."
                    )

                elif password != confirm_password:

                    st.error(
                        "Passwords do not match."
                    )

                else:

                    data, error = register_user(
                        email.strip(),
                        password,
                    )

                    if error:

                        st.error(error)

                    else:

                        # ------------------------------------
                        # Authentication
                        # ------------------------------------

                        st.session_state.authenticated = True

                        st.session_state.access_token = (
                            data["access_token"]
                        )

                        st.session_state.user_email = (
                            data["email"]
                        )

                        st.session_state.user_id = (
                            data["user_id"]
                        )

                        # ------------------------------------
                        # Admin role
                        # ------------------------------------

                        st.session_state.is_admin = bool(
                            data.get("is_admin", False)
                        )

                        if st.session_state.is_admin:
                            st.session_state.user_role = "admin"
                        else:
                            st.session_state.user_role = "user"

                        # ------------------------------------
                        # Default page
                        # ------------------------------------

                        st.session_state.page = "Dashboard"
                        st.session_state.selected_job = None

                        st.rerun()


# ============================================================
# MAIN APPLICATION ROUTER
# ============================================================

if not st.session_state.authenticated:

    show_login()

else:

    # --------------------------------------------------------
    # Sidebar
    # --------------------------------------------------------

    show_sidebar()

    # --------------------------------------------------------
    # Current page
    # --------------------------------------------------------

    page = st.session_state.page

    # ========================================================
    # DASHBOARD
    # ========================================================

    if page == "Dashboard":

        show_dashboard()

    # ========================================================
    # NEW ANALYSIS
    # ========================================================

    elif page == "New Analysis":

        show_new_analysis()

    # ========================================================
    # MY JOBS
    # ========================================================

    elif page == "My Jobs":

        show_jobs()

    # ========================================================
    # REPORTS
    # ========================================================

    elif page == "Reports":

        show_reports()

    # ========================================================
    # PROFILE
    # ========================================================

    elif page == "Profile":

        show_profile()

    # ========================================================
    # ADMIN DASHBOARD
    # ========================================================

    elif page == "Admin Dashboard":

        if st.session_state.get("is_admin", False):

            show_admin_dashboard()

        else:

            st.error(
                "You do not have permission to access "
                "the Admin Dashboard."
            )

    # ========================================================
    # JOB DETAILS
    # ========================================================

    elif page == "Job Details":

        selected_job = st.session_state.get(
            "selected_job"
        )

        if selected_job:

            show_job_details(
                selected_job,
                st.session_state.get("access_token"),
            )

        else:

            st.warning(
                "No job selected."
            )

    # ========================================================
    # INVALID PAGE
    # ========================================================

    else:

        st.session_state.page = "Dashboard"
        st.rerun()