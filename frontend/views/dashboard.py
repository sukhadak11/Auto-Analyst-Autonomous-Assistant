import streamlit as st
import pandas as pd

from components.header import show_header
from services.job_service import fetch_jobs


def show_dashboard():

    show_header(
        "Dashboard",
        "Overview of your automated data analysis activity.",
    )

    access_token = st.session_state.get("access_token")

    if not access_token:
        st.error("Authentication token not found. Please log in again.")
        return

    if st.button("Refresh Dashboard"):
        st.rerun()

    jobs, error = fetch_jobs(access_token)

    if error:
        st.error(error)
        return

    if not jobs:
        st.info("No analysis jobs found.")

        st.write("")
        st.subheader("Get Started")

        if st.button("New Analysis", use_container_width=True):
            st.session_state["page"] = "New Analysis"
            st.rerun()

        return

    # Job statistics
    total_jobs = len(jobs)

    approved_jobs = sum(
        1 for job in jobs
        if job.get("status") == "approved"
    )

    pending_jobs = sum(
        1 for job in jobs
        if job.get("status") in {
            "queued",
            "running",
            "awaiting_approval",
            "needs_revision",
        }
    )

    failed_jobs = sum(
        1 for job in jobs
        if job.get("status") == "failed"
    )

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Jobs", total_jobs)

    with col2:
        st.metric("Approved", approved_jobs)

    with col3:
        st.metric("Pending", pending_jobs)

    with col4:
        st.metric("Failed", failed_jobs)

    st.divider()

    # Quick actions
    st.subheader("Quick Actions")

    action_col1, action_col2 = st.columns(2)

    with action_col1:
        if st.button(
            "New Analysis",
            use_container_width=True,
        ):
            st.session_state["page"] = "New Analysis"
            st.rerun()

    with action_col2:
        if st.button(
            "View Reports",
            use_container_width=True,
        ):
            st.session_state["page"] = "Reports"
            st.rerun()

    st.divider()

    # Recent jobs
    st.subheader("Recent Jobs")

    recent_jobs = jobs[:5]

    for index, job in enumerate(recent_jobs):

        job_id = job.get("job_id", "")
        question = job.get(
            "question",
            "No question provided.",
        )
        status = job.get(
            "status",
            "unknown",
        )
        created_at = job.get(
            "created_at",
            "",
        )

        with st.container(border=True):

            st.write(f"**{question}**")

            col1, col2, col3 = st.columns(3)

            with col1:
                status_display = status.replace(
                    "_",
                    " ",
                ).title()

                st.write(
                    f"**Status:** {status_display}"
                )

            with col2:
                if created_at:
                    st.write(
                        f"**Created:** {created_at}"
                    )
                else:
                    st.write(
                        "**Created:** Not available"
                    )

            with col3:
                if st.button(
                    "View Details",
                    key=f"dashboard_job_{job_id}_{index}",
                    use_container_width=True,
                ):
                    st.session_state["selected_job"] = job_id
                    st.session_state["page"] = "Job Details"
                    st.rerun()