import streamlit as st
import pandas as pd
import requests

API_URL = "http://localhost:8001"
# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AutoAnalyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
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

/* Sidebar */

section[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e6e8ef;
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 2rem;
}

/* Buttons */

.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    min-height: 42px;
}

/* File uploader */

[data-testid="stFileUploader"] {
    background-color: #ffffff;
    border-radius: 10px;
}

/* Hide Streamlit menu/footer */

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

if "user_role" not in st.session_state:
    st.session_state.user_role = "user"

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

if "selected_job" not in st.session_state:
    st.session_state.selected_job = None


# ============================================================
# MOCK DATA
# ============================================================

jobs = pd.DataFrame(
    [
        {
            "Job ID": "8f31a21c",
            "Question": "Analyze customer behavior and identify important factors.",
            "Dataset": "customer_data.csv",
            "Status": "Completed",
            "Created": "Today",
        },
        {
            "Job ID": "91ab72de",
            "Question": "Identify trends and patterns in the dataset.",
            "Dataset": "sales_data.csv",
            "Status": "Running",
            "Created": "Today",
        },
        {
            "Job ID": "32cd91fa",
            "Question": "Find relationships between numerical variables.",
            "Dataset": "business_data.csv",
            "Status": "Completed",
            "Created": "Yesterday",
        },
        {
            "Job ID": "71ef23bc",
            "Question": "Analyze the factors influencing the target outcome.",
            "Dataset": "analysis.csv",
            "Status": "Failed",
            "Created": "Yesterday",
        },
    ]
)


# ============================================================
# LOGIN
# ============================================================

def show_login():
    st.markdown(
        """
        <div style="text-align:center; margin-top:3rem;">
            <h1 style="font-size:2.2rem; margin-bottom:0.3rem;">
                📊 AutoAnalyst
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
        ["🔐 Login", "📝 Create Account"]
    )

    # =========================================================
    # LOGIN
    # =========================================================

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
                    st.warning("Please enter your email.")

                elif not password:
                    st.warning("Please enter your password.")

                else:

                    try:

                        response = requests.post(
                            f"{API_URL}/auth/login",
                            json={
                                "email": email.strip(),
                                "password": password,
                            },
                            timeout=10,
                        )

                        if response.status_code == 200:

                            data = response.json()

                            st.session_state.access_token = data["access_token"]

                            user = get_current_user()

                            if user is None:
                                st.session_state.access_token = None
                                st.error("Unable to retrieve user information.")
                            else:
                                st.session_state.authenticated = True
                                st.session_state.user_email = user["email"]

                                if user["is_admin"]:
                                    st.session_state.user_role = "admin"
                                else:
                                    st.session_state.user_role = "user"

                                st.session_state.page = "Dashboard"

                                st.success("Login successful.")
                                st.rerun()
                        else:

                            try:
                                error_detail = response.json().get(
                                    "detail",
                                    "Login failed."
                                )
                            except Exception:
                                error_detail = "Login failed."

                            st.error(error_detail)

                    except requests.exceptions.ConnectionError:

                        st.error(
                            "Unable to connect to the AutoAnalyst API. "
                            "Make sure FastAPI is running on port 8001."
                        )

                    except requests.exceptions.Timeout:

                        st.error(
                            "The authentication request timed out."
                        )

                    except Exception as e:

                        st.error(
                            f"Login failed: {str(e)}"
                        )

    # =========================================================
    # REGISTER
    # =========================================================

    with register_tab:

        with st.container(border=True):

            st.subheader("Create your account")
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
                    st.warning("Please enter your email.")

                elif not password:
                    st.warning("Please create a password.")

                elif password != confirm_password:
                    st.error("Passwords do not match.")

                else:

                    try:

                        response = requests.post(
                            f"{API_URL}/auth/register",
                            json={
                                "email": email.strip(),
                                "password": password,
                            },
                            timeout=10,
                        )

                        if response.status_code == 200:

                            data = response.json()

                            st.session_state.authenticated = True
                            st.session_state.access_token = data[
                                "access_token"
                            ]
                            st.session_state.user_email = email.strip()
                            st.session_state.user_role = "user"
                            st.session_state.page = "Dashboard"

                            st.success(
                                "Account created successfully."
                            )

                            st.rerun()

                        else:

                            try:
                                error_detail = response.json().get(
                                    "detail",
                                    "Registration failed."
                                )
                            except Exception:
                                error_detail = "Registration failed."

                            st.error(error_detail)

                    except requests.exceptions.ConnectionError:

                        st.error(
                            "Unable to connect to the AutoAnalyst API. "
                            "Make sure FastAPI is running on port 8001."
                        )

                    except requests.exceptions.Timeout:

                        st.error(
                            "The registration request timed out."
                        )

                    except Exception as e:

                        st.error(
                            f"Registration failed: {str(e)}"
                        )    

# ============================================================
# SIDEBAR
# ============================================================

def show_sidebar():

    with st.sidebar:

        st.title("📊 AutoAnalyst")

        st.caption("AUTONOMOUS DATA ANALYSIS")

        st.divider()

        # ----------------------------------------------------
        # Workspace
        # ----------------------------------------------------

        st.caption("WORKSPACE")

        pages = [
            ("🏠", "Dashboard"),
            ("＋", "New Analysis"),
            ("📋", "My Jobs"),
            ("📄", "Reports"),
            ("👤", "Profile"),
        ]

        for icon, page in pages:

            if st.button(
                f"{icon}  {page}",
                key=f"nav_{page}",
                use_container_width=True,
            ):

                st.session_state.page = page
                st.rerun()

        # ----------------------------------------------------
        # Admin Navigation
        # ----------------------------------------------------

        if st.session_state.user_role == "admin":

            st.divider()

            st.caption("ADMINISTRATION")

            if st.button(
                "🛡️  Admin Dashboard",
                key="nav_admin",
                use_container_width=True,
            ):

                st.session_state.page = "Admin Dashboard"
                st.rerun()

        # ----------------------------------------------------
        # User Information
        # ----------------------------------------------------

        st.divider()

        st.caption("SIGNED IN AS")

        st.markdown(
            f"**{st.session_state.user_email}**"
        )

        if st.session_state.user_role == "admin":

            st.caption("🛡️ Administrator")

        else:

            st.caption("👤 Standard User")

        # ----------------------------------------------------
        # Logout
        # ----------------------------------------------------

        if st.button(
            "Logout",
            key="sidebar_logout",
            use_container_width=True,
        ):

            st.session_state.authenticated = False
            st.session_state.user_email = ""
            st.session_state.user_role = "user"
            st.session_state.page = "Dashboard"
            st.session_state.selected_job = None

            st.rerun()


# ============================================================
# PAGE HEADER
# ============================================================

def show_header(title, subtitle):

    st.title(title)

    st.caption(subtitle)


# ============================================================
# METRIC CARD
# ============================================================

def metric_card(title, value, description):

    with st.container(border=True):

        st.caption(title)

        st.metric(
            label="",
            value=value,
        )

        st.caption(description)


# ============================================================
# DASHBOARD
# ============================================================

def show_dashboard():

    show_header(
        "Dashboard",
        "Overview of your automated data analysis activity.",
    )

    # --------------------------------------------------------
    # Calculate metrics from mock jobs
    # --------------------------------------------------------

    total_jobs = len(jobs)

    completed_jobs = len(
        jobs[jobs["Status"] == "Completed"]
    )

    running_jobs = len(
        jobs[jobs["Status"] == "Running"]
    )

    failed_jobs = len(
        jobs[jobs["Status"] == "Failed"]
    )

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        metric_card(
            "Total Jobs",
            total_jobs,
            "All analysis jobs",
        )

    with col2:

        metric_card(
            "Completed",
            completed_jobs,
            "Successfully completed",
        )

    with col3:

        metric_card(
            "Running",
            running_jobs,
            "Currently processing",
        )

    with col4:

        metric_card(
            "Failed",
            failed_jobs,
            "Require attention",
        )

    st.write("")

    # --------------------------------------------------------
    # Recent Analyses + Quick Start
    # --------------------------------------------------------

    col1, col2 = st.columns([2, 1])

    with col1:

        with st.container(border=True):

            st.subheader("Recent Analyses")

            st.caption(
                "Your latest analysis activity"
            )

            recent = jobs.head(4)

            st.dataframe(
                recent[
                    [
                        "Job ID",
                        "Question",
                        "Dataset",
                        "Status",
                        "Created",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

    with col2:

        with st.container(border=True):

            st.subheader("Quick Start")

            st.caption(
                "Start a new analysis"
            )

            st.write(
                "Upload a dataset and ask a business "
                "question. AutoAnalyst will automatically "
                "determine the analysis workflow."
            )

            if st.button(
                "＋ New Analysis",
                use_container_width=True,
                type="primary",
                key="dashboard_new_analysis",
            ):

                st.session_state.page = "New Analysis"
                st.rerun()


# ============================================================
# NEW ANALYSIS
# ============================================================

def show_new_analysis():

    show_header(
        "New Analysis",
        "Upload your dataset and describe what you want to understand.",
    )

    # ========================================================
    # STEP 1 — DATASET
    # ========================================================

    st.subheader("1. Upload Dataset")

    st.caption(
        "Upload the CSV or Excel file you want AutoAnalyst to analyze."
    )

    uploaded_file = st.file_uploader(
        "Choose your dataset",
        type=["csv", "xlsx"],
        label_visibility="collapsed",
    )

    if uploaded_file:

        file_size_mb = uploaded_file.size / (
            1024 * 1024
        )

        st.success(
            f"✓ {uploaded_file.name}  •  "
            f"{file_size_mb:.2f} MB"
        )

        try:

            if uploaded_file.name.lower().endswith(".csv"):

                preview_df = pd.read_csv(
                    uploaded_file
                )

            else:

                preview_df = pd.read_excel(
                    uploaded_file
                )

            with st.expander(
                "Preview dataset",
                expanded=False,
            ):

                st.caption(
                    f"{preview_df.shape[0]:,} rows × "
                    f"{preview_df.shape[1]:,} columns"
                )

                st.dataframe(
                    preview_df.head(10),
                    use_container_width=True,
                    hide_index=True,
                )

        except Exception as e:

            st.warning(
                f"Unable to preview the dataset: {e}"
            )

    st.write("")

    # ========================================================
    # STEP 2 — QUESTION
    # ========================================================

    st.subheader("2. Ask Your Question")

    st.caption(
        "Tell AutoAnalyst what you want to discover from the data."
    )

    question = st.text_area(
        "Business Question",
        placeholder=(
            "Example: What are the key factors influencing "
            "the target outcome?"
        ),
        height=150,
        label_visibility="collapsed",
    )

    st.caption(
        "You can ask about patterns, trends, relationships, "
        "comparisons, predictions, or other insights."
    )

    # ========================================================
    # EXAMPLE QUESTIONS
    # ========================================================

    st.write("")

    st.markdown("#### Need inspiration?")

    example_col1, example_col2, example_col3 = st.columns(3)

    with example_col1:

        with st.container(border=True):

            st.markdown("**📈 Trends & Patterns**")

            st.caption(
                "What trends or patterns can be found "
                "in the dataset?"
            )

    with example_col2:

        with st.container(border=True):

            st.markdown("**🔗 Relationships**")

            st.caption(
                "Which variables have the strongest "
                "relationships?"
            )

    with example_col3:

        with st.container(border=True):

            st.markdown("**🎯 Key Factors**")

            st.caption(
                "Which factors are most important "
                "for the outcome?"
            )

    # ========================================================
    # START ANALYSIS
    # ========================================================

    st.write("")

    if st.button(
        "Start Analysis",
        type="primary",
        use_container_width=True,
        key="start_analysis",
    ):

        if uploaded_file is None:

            st.warning(
                "Please upload a dataset first."
            )

        elif not question.strip():

            st.warning(
                "Please enter an analysis question."
            )

        else:

            st.success(
                "Your analysis is ready to start. "
                "Backend integration will be connected next."
            )


# ============================================================
# MY JOBS
# ============================================================

def show_jobs():

    show_header(
        "My Jobs",
        "View and manage your previous analyses.",
    )

    # --------------------------------------------------------
    # Search and Filter
    # --------------------------------------------------------

    col1, col2 = st.columns([2, 1])

    with col1:

        search = st.text_input(
            "Search jobs",
            placeholder="Search by question or dataset...",
            label_visibility="collapsed",
            key="job_search",
        )

    with col2:

        status_filter = st.selectbox(
            "Status",
            [
                "All",
                "Completed",
                "Running",
                "Failed",
            ],
            label_visibility="collapsed",
            key="job_status_filter",
        )

    st.write("")

    filtered_jobs = jobs.copy()

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    if search:

        mask = (
            filtered_jobs["Question"].str.contains(
                search,
                case=False,
                na=False,
            )
            |
            filtered_jobs["Dataset"].str.contains(
                search,
                case=False,
                na=False,
            )
        )

        filtered_jobs = filtered_jobs[mask]

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    if status_filter != "All":

        filtered_jobs = filtered_jobs[
            filtered_jobs["Status"] == status_filter
        ]

    st.caption(
        f"{len(filtered_jobs)} job(s)"
    )

    # --------------------------------------------------------
    # Job Cards
    # --------------------------------------------------------

    for _, job in filtered_jobs.iterrows():

        with st.container(border=True):

            col1, col2, col3 = st.columns(
                [4, 1.2, 1]
            )

            with col1:

                st.markdown(
                    f"**{job['Question']}**"
                )

                st.caption(
                    f"📄 {job['Dataset']}  •  "
                    f"Job ID: {job['Job ID']}  •  "
                    f"{job['Created']}"
                )

            with col2:

                if job["Status"] == "Completed":

                    st.success("Completed")

                elif job["Status"] == "Running":

                    st.info("Running")

                else:

                    st.error("Failed")

            with col3:

                if st.button(
                    "View",
                    key=f"view_{job['Job ID']}",
                    use_container_width=True,
                ):

                    st.session_state.selected_job = (
                        job["Job ID"]
                    )

                    st.session_state.page = (
                        "Job Details"
                    )

                    st.rerun()


# ============================================================
# REPORTS
# ============================================================

def show_reports():

    show_header(
        "Reports",
        "Access and review your completed analysis reports.",
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    completed_count = len(
        jobs[jobs["Status"] == "Completed"]
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Total Reports",
            completed_count,
        )

    with col2:

        st.metric(
            "Completed",
            completed_count,
        )

    with col3:

        st.metric(
            "Recently Generated",
            min(completed_count, 2),
        )

    st.write("")

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    search = st.text_input(
        "Search reports",
        placeholder="Search by question or dataset...",
        label_visibility="collapsed",
        key="report_search",
    )

    st.write("")

    # --------------------------------------------------------
    # Mock Reports
    # --------------------------------------------------------

    reports = [
        {
            "job_id": "8f31a21c",
            "title": "Customer Behavior Analysis",
            "question": (
                "Analyze customer behavior and "
                "identify important factors."
            ),
            "dataset": "customer_data.csv",
            "date": "Today",
            "findings": "6 important factors identified",
        },
        {
            "job_id": "32cd91fa",
            "title": "Business Relationship Analysis",
            "question": (
                "Find relationships between "
                "numerical variables."
            ),
            "dataset": "business_data.csv",
            "date": "Yesterday",
            "findings": (
                "12 significant relationships found"
            ),
        },
    ]

    # --------------------------------------------------------
    # Search Reports
    # --------------------------------------------------------

    if search:

        reports = [
            report
            for report in reports
            if (
                search.lower()
                in report["title"].lower()
            )
            or (
                search.lower()
                in report["question"].lower()
            )
            or (
                search.lower()
                in report["dataset"].lower()
            )
        ]

    st.caption(
        f"{len(reports)} report(s)"
    )

    # --------------------------------------------------------
    # Report Cards
    # --------------------------------------------------------

    for index, report in enumerate(reports):

        with st.container(border=True):

            col1, col2 = st.columns([4, 1])

            with col1:

                st.markdown(
                    f"### 📄 {report['title']}"
                )

                st.write(
                    report["question"]
                )

                st.caption(
                    f"📊 {report['dataset']}  •  "
                    f"Generated {report['date']}"
                )

                st.caption(
                    f"🔎 {report['findings']}"
                )

            with col2:

                st.success("Completed")

                if st.button(
                    "Open Report",
                    key=f"open_report_{index}",
                    use_container_width=True,
                ):

                    st.session_state.selected_job = (
                        report["job_id"]
                    )

                    st.session_state.page = (
                        "Job Details"
                    )

                    st.rerun()


# ============================================================
# PROFILE
# ============================================================

def show_profile():

    show_header(
        "Profile",
        "View your account information and access settings.",
    )

    # --------------------------------------------------------
    # Account Information
    # --------------------------------------------------------

    st.subheader("Account Information")

    with st.container(border=True):

        col1, col2 = st.columns([1, 2])

        with col1:

            st.markdown("### 👤")

            st.markdown("**Account**")

        with col2:

            st.text_input(
                "Email",
                value=st.session_state.user_email,
                disabled=True,
                key="profile_email",
            )

            role = st.session_state.user_role

            st.text_input(
                "Role",
                value=role.title(),
                disabled=True,
                key="profile_role",
            )

    st.write("")

    # --------------------------------------------------------
    # Account Status
    # --------------------------------------------------------

    st.subheader("Account Status")

    col1, col2 = st.columns(2)

    with col1:

        with st.container(border=True):

            st.markdown("### 🟢 Active")

            st.caption(
                "Your AutoAnalyst account is currently active."
            )

    with col2:

        with st.container(border=True):

            st.markdown("### 🔐 Secure")

            st.caption(
                "Your account is protected by authenticated access."
            )

    st.write("")

    # --------------------------------------------------------
    # Access Information
    # --------------------------------------------------------

    st.subheader("Access & Permissions")

    with st.container(border=True):

        if st.session_state.user_role == "admin":

            st.markdown(
                "### 🛡️ Administrator"
            )

            st.write(
                "You have administrator access."
            )

            st.caption(
                "You can view jobs belonging to all users "
                "and access the Admin Dashboard."
            )

        else:

            st.markdown(
                "### 👤 Standard User"
            )

            st.write(
                "You have standard user access."
            )

            st.caption(
                "You can create analyses and view your own "
                "jobs and reports."
            )

    st.write("")

    # --------------------------------------------------------
    # Account Actions
    # --------------------------------------------------------

    st.subheader("Account Actions")

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "Change Password",
            use_container_width=True,
            key="change_password",
        ):

            st.info(
                "Password management will be connected "
                "during backend integration."
            )

    with col2:

        if st.button(
            "Logout",
            use_container_width=True,
            key="profile_logout",
        ):

            st.session_state.authenticated = False
            st.session_state.user_email = ""
            st.session_state.user_role = "user"
            st.session_state.page = "Dashboard"
            st.session_state.selected_job = None

            st.rerun()


# ============================================================
# ADMIN DASHBOARD
# ============================================================

def show_admin_dashboard():

    show_header(
        "Admin Dashboard",
        "Monitor users, analyses, and overall system activity.",
    )

    # --------------------------------------------------------
    # System Overview
    # --------------------------------------------------------

    st.subheader("System Overview")

    total_users = 24
    total_jobs = 156
    completed_jobs = 132
    running_jobs = 7

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Total Users",
            total_users,
        )

    with col2:

        st.metric(
            "Total Jobs",
            total_jobs,
        )

    with col3:

        st.metric(
            "Completed Jobs",
            completed_jobs,
        )

    with col4:

        st.metric(
            "Running Jobs",
            running_jobs,
        )

    st.write("")

    # --------------------------------------------------------
    # Job Status
    # --------------------------------------------------------

    st.subheader("Job Status")

    status_col1, status_col2, status_col3 = st.columns(3)

    with status_col1:

        with st.container(border=True):

            st.markdown("### ✅ Completed")

            st.metric(
                "Jobs",
                completed_jobs,
            )

            st.caption(
                "Analyses completed successfully."
            )

    with status_col2:

        with st.container(border=True):

            st.markdown("### 🔄 Running")

            st.metric(
                "Jobs",
                running_jobs,
            )

            st.caption(
                "Analyses currently being processed."
            )

    with status_col3:

        with st.container(border=True):

            st.markdown("### ❌ Failed")

            st.metric(
                "Jobs",
                17,
            )

            st.caption(
                "Analyses that encountered an error."
            )

    st.write("")

    # --------------------------------------------------------
    # Recent Jobs
    # --------------------------------------------------------

    st.subheader("Recent Jobs")

    admin_jobs = pd.DataFrame(
        [
            {
                "Job ID": "8f31a21c",
                "User": "user1@example.com",
                "Question": "Analyze customer behavior",
                "Dataset": "customer_data.csv",
                "Status": "Completed",
                "Created": "Today",
            },
            {
                "Job ID": "91ab72de",
                "User": "user2@example.com",
                "Question": "Identify sales trends",
                "Dataset": "sales_data.csv",
                "Status": "Running",
                "Created": "Today",
            },
            {
                "Job ID": "32cd91fa",
                "User": "user3@example.com",
                "Question": "Find variable relationships",
                "Dataset": "business_data.csv",
                "Status": "Completed",
                "Created": "Yesterday",
            },
            {
                "Job ID": "71ef23bc",
                "User": "user4@example.com",
                "Question": "Analyze target factors",
                "Dataset": "analysis.csv",
                "Status": "Failed",
                "Created": "Yesterday",
            },
        ]
    )

    st.dataframe(
        admin_jobs,
        use_container_width=True,
        hide_index=True,
    )

    st.write("")

    # --------------------------------------------------------
    # User Activity
    # --------------------------------------------------------

    st.subheader("User Activity")

    activity_col1, activity_col2 = st.columns(2)

    with activity_col1:

        with st.container(border=True):

            st.markdown("### 👥 Active Users")

            st.metric(
                "Users Active Today",
                12,
            )

            st.caption(
                "Users who created or accessed analyses today."
            )

    with activity_col2:

        with st.container(border=True):

            st.markdown("### 📊 Analyses Today")

            st.metric(
                "New Analyses",
                18,
            )

            st.caption(
                "Analyses submitted today."
            )

    st.write("")

    # --------------------------------------------------------
    # Admin Information
    # --------------------------------------------------------

    with st.expander("Admin Access"):

        st.write(
            "As an administrator, you can view jobs "
            "belonging to all users."
        )

        st.caption(
            "Normal users can only view their own jobs."
        )


# ============================================================
# JOB DETAILS
# ============================================================

def show_job_details():

    job_id = st.session_state.get(
        "selected_job"
    )

    if not job_id:

        st.warning(
            "No job selected."
        )

        if st.button(
            "← Back to My Jobs",
            key="no_job_back",
        ):

            st.session_state.page = "My Jobs"
            st.rerun()

        return

    job = jobs[
        jobs["Job ID"] == job_id
    ]

    if job.empty:

        st.error(
            "Job not found."
        )

        if st.button(
            "← Back to My Jobs",
            key="job_not_found_back",
        ):

            st.session_state.page = "My Jobs"
            st.rerun()

        return

    job = job.iloc[0]

    # --------------------------------------------------------
    # Back Button
    # --------------------------------------------------------

    back_col, _ = st.columns(
        [1, 5]
    )

    with back_col:

        if st.button(
            "← My Jobs",
            use_container_width=True,
            key="job_details_back",
        ):

            st.session_state.page = "My Jobs"
            st.rerun()

    st.write("")

    show_header(
        "Job Details",
        "Review the analysis results and agent decisions.",
    )

    # --------------------------------------------------------
    # Job Summary
    # --------------------------------------------------------

    with st.container(border=True):

        st.markdown("### Analysis Summary")

        col1, col2, col3 = st.columns(3)

        with col1:

            st.caption("STATUS")

            if job["Status"] == "Completed":

                st.success(
                    job["Status"]
                )

            elif job["Status"] == "Running":

                st.info(
                    job["Status"]
                )

            else:

                st.error(
                    job["Status"]
                )

        with col2:

            st.caption("DATASET")

            st.write(
                job["Dataset"]
            )

        with col3:

            st.caption("JOB ID")

            st.code(
                job["Job ID"]
            )

        st.divider()

        st.caption(
            "BUSINESS QUESTION"
        )

        st.write(
            job["Question"]
        )

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    st.write("")

    st.subheader(
        "Analysis Results"
    )

    # ========================================================
    # RUNNING
    # ========================================================

    if job["Status"] == "Running":

        with st.container(border=True):

            st.info(
                "Your analysis is currently running."
            )

            st.progress(
                65
            )

            st.caption(
                "AutoAnalyst is processing the dataset "
                "and generating insights."
            )

    # ========================================================
    # FAILED
    # ========================================================

    elif job["Status"] == "Failed":

        with st.container(border=True):

            st.error(
                "This analysis could not be completed."
            )

            st.caption(
                "The backend will provide detailed error "
                "information once API integration is connected."
            )

    # ========================================================
    # COMPLETED
    # ========================================================

    else:

        # ----------------------------------------------------
        # Key Findings
        # ----------------------------------------------------

        with st.container(border=True):

            st.markdown(
                "### 🔎 Key Findings"
            )

            finding_col1, finding_col2, finding_col3 = (
                st.columns(3)
            )

            with finding_col1:

                st.metric(
                    "Important Factors",
                    "6",
                )

            with finding_col2:

                st.metric(
                    "Relationships Found",
                    "12",
                )

            with finding_col3:

                st.metric(
                    "Visualizations",
                    "4",
                )

            st.write("")

            st.write(
                "The analysis identified several important "
                "patterns and relationships within the dataset."
            )

        st.write("")

        # ----------------------------------------------------
        # Visualizations
        # ----------------------------------------------------

        st.markdown(
            "### 📊 Visualizations"
        )

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:

            with st.container(border=True):

                st.markdown(
                    "**Feature Importance**"
                )

                feature_data = pd.DataFrame(
                    {
                        "Importance": [
                            82,
                            68,
                            55,
                            43,
                            31,
                        ]
                    },
                    index=[
                        "Feature A",
                        "Feature B",
                        "Feature C",
                        "Feature D",
                        "Feature E",
                    ],
                )

                st.bar_chart(
                    feature_data
                )

        with chart_col2:

            with st.container(border=True):

                st.markdown(
                    "**Target Distribution**"
                )

                target_data = pd.DataFrame(
                    {
                        "Count": [
                            520,
                            310,
                        ]
                    },
                    index=[
                        "Category A",
                        "Category B",
                    ],
                )

                st.bar_chart(
                    target_data
                )

        st.write("")

        # ----------------------------------------------------
        # Report
        # ----------------------------------------------------

        st.markdown(
            "### 📄 Report"
        )

        with st.container(border=True):

            st.write(
                "The analysis provides an overview of the dataset, "
                "important variables, relationships, and key patterns."
            )

            st.write(
                "AutoAnalyst automatically selected the appropriate "
                "analysis workflow based on the business question "
                "and dataset."
            )

            if st.button(
                "View Full Report",
                key="view_full_report",
            ):

                st.info(
                    "Full report viewer will be connected "
                    "during backend integration."
                )

        st.write("")

        # ----------------------------------------------------
        # Agent Decisions
        # ----------------------------------------------------

        st.markdown(
            "### 🤖 Agent Decisions"
        )

        with st.expander(
            "View how AutoAnalyst made its decisions"
        ):

            st.markdown(
                "**Planner**"
            )

            st.caption(
                "Selected the analysis agents required "
                "for the business question."
            )

            st.markdown(
                "**Profiling Agent**"
            )

            st.caption(
                "Inspected the uploaded dataset and "
                "identified its structure and characteristics."
            )

            st.markdown(
                "**Modeling Agent**"
            )

            st.caption(
                "Selected an appropriate modeling approach "
                "based on the dataset."
            )

            st.markdown(
                "**Visualization Agent**"
            )

            st.caption(
                "Selected visualizations based on the "
                "actual dataset and analysis requirements."
            )

            st.markdown(
                "**Report Agent**"
            )

            st.caption(
                "Combined the analysis results into a "
                "final report."
            )

        st.write("")

        # ----------------------------------------------------
        # Critique
        # ----------------------------------------------------

        st.markdown(
            "### 🧐 Critique"
        )

        with st.container(border=True):

            st.caption(
                "CRITIC AGENT"
            )

            st.write(
                "The generated analysis was reviewed for "
                "completeness, consistency, and relevance."
            )

            st.success(
                "Analysis approved"
            )

        st.write("")

        # ----------------------------------------------------
        # Human Approval
        # ----------------------------------------------------

        st.markdown(
            "### ✅ Approval"
        )

        with st.container(border=True):

            st.write(
                "Review the generated analysis before "
                "final approval."
            )

            approval_col1, approval_col2 = (
                st.columns(2)
            )

            with approval_col1:

                if st.button(
                    "Approve Analysis",
                    type="primary",
                    use_container_width=True,
                    key="approve_analysis",
                ):

                    st.success(
                        "Analysis approved."
                    )

            with approval_col2:

                if st.button(
                    "Request Revision",
                    use_container_width=True,
                    key="request_revision",
                ):

                    st.warning(
                        "Revision requested."
                    )


# ============================================================
# PAGE ROUTER
# ============================================================

if not st.session_state.authenticated:

    show_login()

else:

    show_sidebar()

    page = st.session_state.page

    if page == "Dashboard":

        show_dashboard()

    elif page == "New Analysis":

        show_new_analysis()

    elif page == "My Jobs":

        show_jobs()

    elif page == "Reports":

        show_reports()

    elif page == "Profile":

        show_profile()

    elif page == "Admin Dashboard":

        # Temporary frontend protection
        if st.session_state.user_role == "admin":

            show_admin_dashboard()

        else:

            st.error(
                "You do not have permission to access "
                "the Admin Dashboard."
            )

            st.session_state.page = "Dashboard"

    elif page == "Job Details":

        show_job_details()

    else:

        st.session_state.page = "Dashboard"
        st.rerun()

def get_current_user():
    token = st.session_state.get("access_token")

    if not token:
        return None

    try:
        response = requests.get(
            f"{API_URL}/auth/me",
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=10,
        )

        if response.status_code == 200:
            return response.json()

        return None

    except requests.exceptions.RequestException:
        return None        