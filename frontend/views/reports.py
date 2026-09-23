import streamlit as st
import requests

from components.header import show_header
from services.job_service import fetch_reports, get_job_status, get_headers, API_BASE_URL


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
            # Dataset Preview
            # ------------------------------------------------

            if job_id:

                try:
                    job_status = get_job_status(
                        job_id,
                        access_token
                    )

                    dataset = job_status.get(
                        "dataset",
                        {}
                    )

                    if dataset:

                        st.markdown(
                            "### Dataset"
                        )

                        dataset_col1, dataset_col2, dataset_col3 = st.columns(3)

                        with dataset_col1:
                            st.write(
                                f"**Filename:** "
                                f"{dataset.get('filename', 'Not available')}"
                            )

                        with dataset_col2:
                            st.write(
                                f"**Rows:** "
                                f"{dataset.get('rows', 'Not available')}"
                            )

                        with dataset_col3:
                            st.write(
                                f"**Columns:** "
                                f"{dataset.get('columns', 'Not available')}"
                            )

                        preview = dataset.get(
                            "preview",
                            []
                        )

                        if preview:
                            st.dataframe(
                                preview,
                                use_container_width=True,
                                hide_index=True
                            )
                        else:
                            st.info(
                                "Dataset preview is not available."
                            )

                except Exception as e:
                    st.warning(
                        f"Unable to load dataset preview: {e}"
                    )

                # ------------------------------------------------
                # Downloads
                # ------------------------------------------------

                st.markdown(
                    "### Downloads"
                )

                download_col1, download_col2 = st.columns(2)

                with download_col1:

                    try:
                        csv_response = requests.get(
                            f"{API_BASE_URL}/download/{job_id}/csv",
                            headers=get_headers(access_token),
                            timeout=30
                        )

                        if csv_response.status_code == 200:
                            st.download_button(
                                label="Download Processed CSV",
                                data=csv_response.content,
                                file_name="cleaned_data.csv",
                                mime="text/csv",
                                key=f"download_csv_{job_id}_{index}",
                                use_container_width=True
                            )
                        else:
                            st.warning(
                                "Processed CSV is not available."
                            )

                    except requests.RequestException:
                        st.warning(
                            "Unable to download the processed CSV."
                        )

                with download_col2:

                    try:
                        model_response = requests.get(
                            f"{API_BASE_URL}/download/{job_id}/model",
                            headers=get_headers(access_token),
                            timeout=30
                        )

                        if model_response.status_code == 200:
                            st.download_button(
                                label="Download Trained Model",
                                data=model_response.content,
                                file_name="trained_model.joblib",
                                mime="application/octet-stream",
                                key=f"download_model_{job_id}_{index}",
                                use_container_width=True
                            )
                        else:
                            st.warning(
                                "Trained model is not available."
                            )

                    except requests.RequestException:
                        st.warning(
                            "Unable to download the trained model."
                        )

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