import streamlit as st

from components.header import show_header

from services.admin_service import (
    fetch_admin_dashboard,
    fetch_admin_users,
    fetch_admin_jobs,
)

from services.job_service import (
    delete_job,
)


def show_admin_dashboard():

    # ========================================================
    # ADMIN ACCESS CHECK
    # ========================================================

    if not st.session_state.get(
        "is_admin",
        False,
    ):

        st.error(
            "You do not have permission "
            "to access the Admin Dashboard."
        )

        return

    # ========================================================
    # HEADER
    # ========================================================

    show_header(
        "Admin Dashboard",
        "Monitor users, analysis jobs, and application activity.",
    )

    access_token = st.session_state.get(
        "access_token"
    )

    if not access_token:

        st.error(
            "Authentication token not found. "
            "Please log in again."
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
    # DASHBOARD STATISTICS
    # ========================================================

    dashboard_data, dashboard_error = (
        fetch_admin_dashboard(
            access_token
        )
    )

    if dashboard_error:

        st.error(
            dashboard_error
        )

        return

    if not dashboard_data:

        st.warning(
            "No dashboard data is available."
        )

        return

    users_data = dashboard_data.get(
        "users",
        {},
    )

    jobs_data = dashboard_data.get(
        "jobs",
        {},
    )

    # ========================================================
    # USER STATISTICS
    # ========================================================

    st.subheader(
        "User Overview"
    )

    user_col1, user_col2, user_col3, user_col4 = (
        st.columns(4)
    )

    with user_col1:

        st.metric(
            "Total Users",
            users_data.get(
                "total",
                0,
            ),
        )

    with user_col2:

        st.metric(
            "Active Users",
            users_data.get(
                "active",
                0,
            ),
        )

    with user_col3:

        st.metric(
            "Admin Users",
            users_data.get(
                "admins",
                0,
            ),
        )

    with user_col4:

        st.metric(
            "Normal Users",
            users_data.get(
                "normal_users",
                0,
            ),
        )

    st.divider()

    # ========================================================
    # JOB STATISTICS
    # ========================================================

    st.subheader(
        "Job Overview"
    )

    job_col1, job_col2, job_col3, job_col4 = (
        st.columns(4)
    )

    with job_col1:

        st.metric(
            "Total Jobs",
            jobs_data.get(
                "total",
                0,
            ),
        )

    with job_col2:

        st.metric(
            "Queued",
            jobs_data.get(
                "queued",
                0,
            ),
        )

    with job_col3:

        st.metric(
            "Running",
            jobs_data.get(
                "running",
                0,
            ),
        )

    with job_col4:

        st.metric(
            "Awaiting Approval",
            jobs_data.get(
                "awaiting_approval",
                0,
            ),
        )

    job_col5, job_col6, job_col7, job_col8 = (
        st.columns(4)
    )

    with job_col5:

        st.metric(
            "Approved",
            jobs_data.get(
                "approved",
                0,
            ),
        )

    with job_col6:

        st.metric(
            "Rejected",
            jobs_data.get(
                "rejected",
                0,
            ),
        )

    with job_col7:

        st.metric(
            "Needs Revision",
            jobs_data.get(
                "needs_revision",
                0,
            ),
        )

    with job_col8:

        st.metric(
            "Failed",
            jobs_data.get(
                "failed",
                0,
            ),
        )

    st.divider()

    # ========================================================
    # USERS
    # ========================================================

    st.subheader(
        "Users"
    )

    users, users_error = fetch_admin_users(
        access_token
    )

    if users_error:

        st.error(
            users_error
        )

    elif not users:

        st.info(
            "No users found."
        )

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
                        if user.get(
                            "is_admin",
                            False,
                        )
                        else "User"
                    ),
                    "Active": (
                        "Yes"
                        if user.get(
                            "is_active",
                            False,
                        )
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

    st.subheader(
        "All Analysis Jobs"
    )

    jobs, jobs_error = fetch_admin_jobs(
        access_token
    )

    if jobs_error:

        st.error(
            jobs_error
        )

    elif not jobs:

        st.info(
            "No analysis jobs found."
        )

    else:

        # ----------------------------------------------------
        # ADMIN DELETE CONFIRMATION
        # ----------------------------------------------------

        admin_confirm_delete_job = (
            st.session_state.get(
                "admin_confirm_delete_job"
            )
        )

        if admin_confirm_delete_job:

            st.warning(
                "Are you sure you want to delete "
                f"job {admin_confirm_delete_job}?"
            )

            st.caption(
                "This will permanently remove the "
                "job, uploaded dataset, generated charts, "
                "and trained model."
            )

            confirm_col1, confirm_col2 = (
                st.columns(2)
            )

            with confirm_col1:

                if st.button(
                    "Confirm Delete",
                    type="primary",
                    use_container_width=True,
                    key="admin_confirm_delete",
                ):

                    try:

                        delete_job(
                            admin_confirm_delete_job,
                            access_token,
                        )

                        st.session_state[
                            "admin_confirm_delete_job"
                        ] = None

                        if (
                            st.session_state.get(
                                "selected_job"
                            )
                            == admin_confirm_delete_job
                        ):

                            st.session_state[
                                "selected_job"
                            ] = None

                        st.success(
                            "Job deleted successfully."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"Failed to delete job: {e}"
                        )

            with confirm_col2:

                if st.button(
                    "Cancel",
                    use_container_width=True,
                    key="admin_cancel_delete",
                ):

                    st.session_state[
                        "admin_confirm_delete_job"
                    ] = None

                    st.rerun()

            st.divider()

        # ----------------------------------------------------
        # JOB CARDS
        # ----------------------------------------------------

        for index, job in enumerate(jobs):

            job_id = job.get(
                "job_id",
                "",
            )

            user_id = job.get(
                "user_id",
                "",
            )

            question = job.get(
                "question",
                "",
            )

            status = job.get(
                "status",
                "",
            )

            dataset_type = job.get(
                "dataset_type",
                "",
            )

            model_name = job.get(
                "model_name",
                "",
            )

            created_at = job.get(
                "created_at",
                "",
            )

            status_display = (
                status
                .replace("_", " ")
                .title()
            )

            with st.container(
                border=True
            ):

                st.write(
                    f"**{question}**"
                )

                info_col1, info_col2, info_col3 = (
                    st.columns(3)
                )

                with info_col1:

                    st.write(
                        f"**Job ID:** `{job_id}`"
                    )

                    st.write(
                        f"**User ID:** `{user_id}`"
                    )

                with info_col2:

                    st.write(
                        f"**Status:** {status_display}"
                    )

                    st.write(
                        f"**Dataset Type:** "
                        f"{dataset_type or 'Not available'}"
                    )

                with info_col3:

                    st.write(
                        f"**Model:** "
                        f"{model_name or 'Not available'}"
                    )

                    st.write(
                        f"**Created:** "
                        f"{created_at or 'Not available'}"
                    )

                st.write("")

                action_col1, action_col2 = (
                    st.columns(2)
                )

                with action_col1:

                    if st.button(
                        "View Job Details",
                        key=(
                            f"admin_view_"
                            f"{job_id}_{index}"
                        ),
                        use_container_width=True,
                    ):

                        st.session_state[
                            "selected_job"
                        ] = job_id

                        st.session_state[
                            "page"
                        ] = "Job Details"

                        st.rerun()

                with action_col2:

                    if st.button(
                        "Delete Job",
                        key=(
                            f"admin_delete_"
                            f"{job_id}_{index}"
                        ),
                        use_container_width=True,
                    ):

                        st.session_state[
                            "admin_confirm_delete_job"
                        ] = job_id

                        st.rerun()