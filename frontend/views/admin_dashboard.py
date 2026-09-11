import streamlit as st

from components.header import show_header
from services.admin_service import (
    fetch_admin_dashboard,
    fetch_admin_users,
    fetch_admin_jobs,
)


def show_admin_dashboard():
    """
    Display the administrator dashboard.

    Only admin users should be able to access this page.
    """

    # ========================================================
    # ADMIN ACCESS CHECK
    # ========================================================

    if not st.session_state.get("is_admin", False):
        st.error(
            "You do not have permission to access the Admin Dashboard."
        )
        return

    # ========================================================
    # HEADER
    # ========================================================

    show_header(
        "Admin Dashboard",
        "Monitor users, analysis jobs, and application activity.",
    )

    access_token = st.session_state.get("access_token")

    if not access_token:
        st.error(
            "Authentication token not found. Please log in again."
        )
        return

    # ========================================================
    # REFRESH
    # ========================================================

    if st.button(
        "Refresh Dashboard",
        use_container_width=False,
    ):
        st.rerun()

    st.write("")

    # ========================================================
    # FETCH DASHBOARD STATISTICS
    # ========================================================

    dashboard_data, dashboard_error = fetch_admin_dashboard(
        access_token
    )

    if dashboard_error:
        st.error(dashboard_error)
        return

    if not dashboard_data:
        st.warning(
            "No dashboard data is available."
        )
        return

    users_data = dashboard_data.get(
        "users",
        {}
    )

    jobs_data = dashboard_data.get(
        "jobs",
        {}
    )

    # ========================================================
    # USER STATISTICS
    # ========================================================

    st.subheader("User Overview")

    user_col1, user_col2, user_col3, user_col4 = st.columns(4)

    with user_col1:
        st.metric(
            "Total Users",
            users_data.get("total", 0),
        )

    with user_col2:
        st.metric(
            "Active Users",
            users_data.get("active", 0),
        )

    with user_col3:
        st.metric(
            "Admin Users",
            users_data.get("admins", 0),
        )

    with user_col4:
        st.metric(
            "Normal Users",
            users_data.get("normal_users", 0),
        )

    st.divider()

    # ========================================================
    # JOB STATISTICS
    # ========================================================

    st.subheader("Job Overview")

    job_col1, job_col2, job_col3, job_col4 = st.columns(4)

    with job_col1:
        st.metric(
            "Total Jobs",
            jobs_data.get("total", 0),
        )

    with job_col2:
        st.metric(
            "Queued",
            jobs_data.get("queued", 0),
        )

    with job_col3:
        st.metric(
            "Running",
            jobs_data.get("running", 0),
        )

    with job_col4:
        st.metric(
            "Awaiting Approval",
            jobs_data.get("awaiting_approval", 0),
        )

    job_col5, job_col6, job_col7, job_col8 = st.columns(4)

    with job_col5:
        st.metric(
            "Approved",
            jobs_data.get("approved", 0),
        )

    with job_col6:
        st.metric(
            "Rejected",
            jobs_data.get("rejected", 0),
        )

    with job_col7:
        st.metric(
            "Needs Revision",
            jobs_data.get("needs_revision", 0),
        )

    with job_col8:
        st.metric(
            "Failed",
            jobs_data.get("failed", 0),
        )

    st.divider()

    # ========================================================
    # USERS
    # ========================================================

    st.subheader("Users")

    users, users_error = fetch_admin_users(
        access_token
    )

    if users_error:

        st.error(users_error)

    elif not users:

        st.info("No users found.")

    else:

        user_rows = []

        for user in users:

            user_rows.append(
                {
                    "User ID": user.get(
                        "user_id",
                        "",
                    ),
                    "Email": user.get(
                        "email",
                        "",
                    ),
                    "Role": (
                        "Admin"
                        if user.get("is_admin", False)
                        else "User"
                    ),
                    "Active": (
                        "Yes"
                        if user.get("is_active", False)
                        else "No"
                    ),
                    "Jobs": user.get(
                        "job_count",
                        0,
                    ),
                    "Created": user.get(
                        "created_at",
                        "",
                    ),
                }
            )

        st.dataframe(
            user_rows,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    # ========================================================
    # ALL JOBS
    # ========================================================

    st.subheader("All Analysis Jobs")

    jobs, jobs_error = fetch_admin_jobs(
        access_token
    )

    if jobs_error:

        st.error(jobs_error)

    elif not jobs:

        st.info("No analysis jobs found.")

    else:

        job_rows = []

        for job in jobs:

            job_rows.append(
                {
                    "Job ID": job.get(
                        "job_id",
                        "",
                    ),
                    "User ID": job.get(
                        "user_id",
                        "",
                    ),
                    "Question": job.get(
                        "question",
                        "",
                    ),
                    "Status": (
                        job.get(
                            "status",
                            "",
                        )
                        .replace("_", " ")
                        .title()
                    ),
                    "Dataset Type": job.get(
                        "dataset_type",
                        "",
                    ),
                    "Model": job.get(
                        "model_name",
                        "",
                    ),
                    "Created": job.get(
                        "created_at",
                        "",
                    ),
                }
            )

        st.dataframe(
            job_rows,
            use_container_width=True,
            hide_index=True,
        )