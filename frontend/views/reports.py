import streamlit as st

from components.header import show_header
from services.job_service import fetch_reports


def show_reports():
    """
    Display completed analysis reports.

    Admin users can see all available reports.
    Normal users can see only their own reports.
    """

    show_header(
        "Reports",
        "Access and review your completed analysis reports.",
    )

    access_token = st.session_state.get("access_token")

    if not access_token:
        st.error(
            "Authentication token not found. Please log in again."
        )
        return

    # --------------------------------------------------------
    # Fetch reports
    # --------------------------------------------------------

    reports, error = fetch_reports(access_token)

    if error:
        st.error(error)
        return

    # --------------------------------------------------------
    # No reports
    # --------------------------------------------------------

    if not reports:
        st.info(
            "No completed analysis reports are available yet."
        )
        return

    # --------------------------------------------------------
    # Refresh
    # --------------------------------------------------------

    if st.button(
        "Refresh Reports",
        use_container_width=False,
    ):
        st.rerun()

    st.write("")

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    st.metric(
        "Available Reports",
        len(reports),
    )

    st.divider()

    # --------------------------------------------------------
    # Reports list
    # --------------------------------------------------------

    for index, report in enumerate(reports):

        job_id = report.get(
            "job_id",
            "",
        )

        question = report.get(
            "question",
            "Analysis Report",
        )

        status = report.get(
            "status",
            "approved",
        )

        dataset_type = report.get(
            "dataset_type",
            "Unknown",
        )

        model_name = report.get(
            "model_name",
            "Not available",
        )

        created_at = report.get(
            "created_at",
            "",
        )

        report_content = report.get(
            "report",
            "",
        )

        # ----------------------------------------------------
        # Report container
        # ----------------------------------------------------

        with st.container(border=True):

            st.subheader(question)

            # Metadata
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write(
                    f"**Status:** "
                    f"{status.replace('_', ' ').title()}"
                )

            with col2:
                st.write(
                    f"**Dataset Type:** {dataset_type}"
                )

            with col3:
                st.write(
                    f"**Model:** {model_name}"
                )

            if created_at:
                st.write(
                    f"**Created:** {created_at}"
                )

            if job_id:
                st.write(
                    f"**Job ID:** `{job_id}`"
                )

            st.divider()

            # ------------------------------------------------
            # Report content
            # ------------------------------------------------

            if report_content:

                st.markdown(
                    "### Analysis Report"
                )

                st.markdown(
                    report_content
                )

            else:
                st.info(
                    "No report content is available."
                )

            st.write("")

            # ------------------------------------------------
            # Open Job Details
            # ------------------------------------------------

            if job_id:

                if st.button(
                    "View Job Details",
                    key=f"report_job_{job_id}_{index}",
                    use_container_width=True,
                ):
                    st.session_state[
                        "selected_job"
                    ] = job_id

                    st.session_state[
                        "page"
                    ] = "Job Details"

                    st.rerun()