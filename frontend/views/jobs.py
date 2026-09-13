import streamlit as st

from components.header import show_header

from services.job_service import (
    fetch_jobs,
    delete_job,
)


def show_jobs():

    show_header(
        "My Jobs",
        "View and track your analysis jobs.",
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
    # FETCH JOBS
    # ========================================================

    jobs, error = fetch_jobs(
        access_token
    )

    if error:

        st.error(error)

        return

    # ========================================================
    # NO JOBS
    # ========================================================

    if not jobs:

        st.info(
            "No analysis jobs found."
        )

        return

    # ========================================================
    # REFRESH
    # ========================================================

    if st.button(
        "Refresh Jobs",
        use_container_width=False,
    ):

        st.rerun()

    st.write("")

    # ========================================================
    # JOB STATISTICS
    # ========================================================

    total_jobs = len(jobs)

    completed_jobs = sum(
        1
        for job in jobs
        if job.get("status") == "approved"
    )

    pending_jobs = sum(
        1
        for job in jobs
        if job.get("status")
        in {
            "queued",
            "running",
            "awaiting_approval",
            "needs_revision",
        }
    )

    failed_jobs = sum(
        1
        for job in jobs
        if job.get("status") == "failed"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Total Jobs",
            total_jobs,
        )

    with col2:

        st.metric(
            "Approved",
            completed_jobs,
        )

    with col3:

        st.metric(
            "Pending",
            pending_jobs,
        )

    with col4:

        st.metric(
            "Failed",
            failed_jobs,
        )

    st.divider()

    # ========================================================
    # DELETE CONFIRMATION
    # ========================================================

    confirm_delete_job = st.session_state.get(
        "confirm_delete_job"
    )

    if confirm_delete_job:

        st.warning(
            "Are you sure you want to delete this job? "
            "The uploaded dataset, generated charts, "
            "trained model, and job record will be removed."
        )

        confirm_col1, confirm_col2 = st.columns(2)

        with confirm_col1:

            if st.button(
                "Confirm Delete",
                type="primary",
                use_container_width=True,
                key="confirm_delete_button",
            ):

                try:

                    delete_job(
                        confirm_delete_job,
                        access_token,
                    )

                    st.session_state[
                        "confirm_delete_job"
                    ] = None

                    if (
                        st.session_state.get(
                            "selected_job"
                        )
                        == confirm_delete_job
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
                key="cancel_delete_button",
            ):

                st.session_state[
                    "confirm_delete_job"
                ] = None

                st.rerun()

        st.divider()

    # ========================================================
    # JOB LIST
    # ========================================================

    for index, job in enumerate(jobs):

        job_id = job.get(
            "job_id",
            "",
        )

        question = job.get(
            "question",
            "No question provided.",
        )

        status = job.get(
            "status",
            "unknown",
        )

        user_id = job.get(
            "user_id",
            "",
        )

        created_at = job.get(
            "created_at",
            "",
        )

        with st.container(
            border=True
        ):

            st.subheader(
                question
            )

            status_display = (
                status
                .replace("_", " ")
                .title()
            )

            st.write(
                f"**Status:** {status_display}"
            )

            metadata_col1, metadata_col2, metadata_col3 = (
                st.columns(3)
            )

            with metadata_col1:

                st.write(
                    f"**Job ID:** `{job_id}`"
                )

            with metadata_col2:

                if created_at:

                    st.write(
                        f"**Created:** {created_at}"
                    )

                else:

                    st.write(
                        "**Created:** Not available"
                    )

            with metadata_col3:

                if user_id:

                    st.write(
                        f"**User ID:** `{user_id}`"
                    )

            st.write("")

            action_col1, action_col2 = (
                st.columns(2)
            )

            with action_col1:

                if st.button(
                    "View Job Details",
                    key=f"view_job_{job_id}_{index}",
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
                    key=f"delete_job_{job_id}_{index}",
                    use_container_width=True,
                ):

                    st.session_state[
                        "confirm_delete_job"
                    ] = job_id

                    st.rerun()