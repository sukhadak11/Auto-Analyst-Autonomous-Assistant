import streamlit as st
import requests
import time

from services.job_service import (
    get_job_status,
    approve_job,
    reprocess_job,
)

API_BASE_URL = "http://127.0.0.1:8001"


# =========================================================
# Authentication
# =========================================================

def _get_access_token():
    """Get authentication token from Streamlit session state."""
    return st.session_state.get("access_token")


# =========================================================
# API Helpers
# =========================================================

def _get_job_status(job_id: str, access_token: str):
    """Fetch the latest job status."""
    return get_job_status(job_id, access_token)


def _approve_job(
    job_id: str,
    decision: str,
    notes: str,
    access_token: str,
):
    """Submit human approval decision."""
    return approve_job(
        job_id,
        decision,
        notes,
        access_token,
    )


def _reprocess_job(
    job_id: str,
    access_token: str,
):
    """Reprocess an existing job in needs_revision state."""
    return reprocess_job(
        job_id,
        access_token,
    )


def _download_chart(
    job_id: str,
    filename: str,
    access_token: str,
):
    """Download a chart from the authenticated backend."""

    try:
        response = requests.get(
            f"{API_BASE_URL}/charts/{job_id}/{filename}",
            headers={
                "Authorization": f"Bearer {access_token}"
            },
            timeout=30,
        )

        if response.status_code == 200:
            return response.content

    except requests.RequestException:
        pass

    return None


# =========================================================
# Response Helpers
# =========================================================

def _get_result_data(job_data):
    """
    Handle different possible API response structures.

    Supports:
        {
            "status": "...",
            "report": "..."
        }

    and:

        {
            "status": "...",
            "result": {
                "report": "..."
            }
        }

    and:

        {
            "status": "...",
            "job": {
                "report": "..."
            }
        }
    """

    if not isinstance(job_data, dict):
        return {}

    if isinstance(job_data.get("result"), dict):
        return job_data["result"]

    if isinstance(job_data.get("job"), dict):
        return job_data["job"]

    return job_data


def _get_field(job_data, field_names, default=None):
    """
    Get a field from the main response or nested result/job response.
    """

    if not isinstance(job_data, dict):
        return default

    nested_data = _get_result_data(job_data)

    for field in field_names:

        value = job_data.get(field)

        if value is not None and value != "":
            return value

        value = nested_data.get(field)

        if value is not None and value != "":
            return value

    return default


# =========================================================
# Status
# =========================================================

def _display_status(status: str):
    """Display a readable status message."""

    if status == "queued":

        st.info("Job is queued.")

    elif status == "running":

        st.info("Job is currently running.")

    elif status == "awaiting_approval":

        st.warning(
            "This job is waiting for human approval."
        )

    elif status == "needs_revision":

        st.warning(
            "This job requires revision."
        )

    elif status == "approved":

        st.success(
            "This job has been approved."
        )

    elif status == "rejected":

        st.error(
            "This job has been rejected."
        )

    elif status == "failed":

        st.error(
            "Job processing failed."
        )

    else:

        st.info(
            f"Status: {status}"
        )


# =========================================================
# Dataset Information
# =========================================================

def _display_dataset_information(job_data):

    """Display dataset and model information."""

    st.subheader("Dataset Information")

    dataset_type = _get_field(
        job_data,
        ["dataset_type"],
        "Not available",
    )

    target_column = _get_field(
        job_data,
        ["target_column", "target_col"],
        "Not specified",
    )

    model_name = _get_field(
        job_data,
        ["model_name", "model"],
        "Not available",
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown("**Dataset Type**")
        st.write(dataset_type)

    with col2:

        st.markdown("**Target Column**")
        st.write(target_column)

    with col3:

        st.markdown("**Model**")
        st.write(model_name)


# =========================================================
# Report
# =========================================================

def _display_report(job_data):

    """Display generated analysis report."""

    report = _get_field(
        job_data,
        ["report"],
    )

    st.subheader("Analysis Report")

    if report:

        st.markdown(report)

    else:

        st.info(
            "No report is available yet."
        )


# =========================================================
# Visualizations
# =========================================================

def _display_visualizations(
    job_id: str,
    job_data,
    access_token: str,
):

    """Display generated visualization charts."""

    charts = _get_field(
        job_data,
        ["generated_charts", "charts"],
        [],
    )

    if not charts:
        charts = []

    st.subheader("Visualizations")

    if not charts:

        st.info(
            "No visualizations were generated "
            "for this analysis."
        )

        return

    for index, chart in enumerate(
        charts,
        start=1,
    ):

        if isinstance(chart, dict):

            filename = (
                chart.get("filename")
                or chart.get("file")
                or chart.get("name")
            )

            title = (
                chart.get("title")
                or chart.get("chart_type")
                or f"Visualization {index}"
            )

        else:

            filename = str(chart)
            title = f"Visualization {index}"

        if not filename:
            continue

        st.markdown(
            f"### {title}"
        )

        image_bytes = _download_chart(
            job_id,
            filename,
            access_token,
        )

        if image_bytes:

            st.image(
                image_bytes,
                use_container_width=True,
            )

        else:

            st.warning(
                f"Unable to load visualization: "
                f"{filename}"
            )


# =========================================================
# Agent Explanations
# =========================================================

def _display_explanations(job_data):

    """Display agent decision/explanation information."""

    explanations = _get_field(
        job_data,
        ["explanations"],
        [],
    )

    if not explanations:
        explanations = []

    st.subheader("Agent Decisions")

    if not explanations:

        st.info(
            "No agent decisions were recorded."
        )

        return

    for index, explanation in enumerate(
        explanations,
        start=1,
    ):

        if isinstance(explanation, dict):

            action = explanation.get(
                "action",
                "Decision",
            )

            reason = explanation.get(
                "reason",
                "",
            )

            alternative = explanation.get(
                "alternative_considered",
                "",
            )

            why_not = explanation.get(
                "why_not_chosen",
                "",
            )

            impact = explanation.get(
                "expected_impact",
                "",
            )

            learning = explanation.get(
                "learning_note",
                "",
            )

            confidence = explanation.get(
                "confidence",
                "",
            )

            with st.expander(
                f"{index}. {action}"
            ):

                if reason:

                    st.markdown("**Reason**")
                    st.write(reason)

                if alternative:

                    st.markdown(
                        "**Alternative Considered**"
                    )

                    st.write(alternative)

                if why_not:

                    st.markdown(
                        "**Why Not Chosen**"
                    )

                    st.write(why_not)

                if impact:

                    st.markdown(
                        "**Expected Impact**"
                    )

                    st.write(impact)

                if learning:

                    st.markdown(
                        "**Learning Note**"
                    )

                    st.write(learning)

                if confidence:

                    st.markdown(
                        "**Confidence**"
                    )

                    st.write(confidence)

        else:

            st.write(
                explanation
            )


# =========================================================
# Critique
# =========================================================

def _display_critique(job_data):

    """Display critic feedback."""

    critique = _get_field(
        job_data,
        ["critique"],
    )

    st.subheader("Critique")

    if critique:

        st.write(critique)

    else:

        st.info(
            "No critique is available."
        )


# =========================================================
# Human Review History
# =========================================================

def _display_human_review_history(job_data):

    """Display previous human review information."""

    human_decision = _get_field(
        job_data,
        ["human_decision"],
    )

    human_notes = _get_field(
        job_data,
        ["human_notes"],
    )

    if not human_decision and not human_notes:
        return

    st.subheader("Human Review")

    if human_decision:

        st.markdown("**Decision**")
        st.write(human_decision)

    if human_notes:

        st.markdown("**Review Notes**")
        st.write(human_notes)


# =========================================================
# Human Approval
# =========================================================

def _display_human_approval(
    job_id: str,
    job_data,
    access_token: str,
):

    """
    Human approval and revision workflow.

    awaiting_approval:
        Approve / Needs Revision / Reject

    needs_revision:
        Reprocess Revision
    """

    st.subheader("Human Approval")

    current_status = job_data.get(
        "status",
        "",
    )

    # -----------------------------------------------------
    # Awaiting Approval
    # -----------------------------------------------------

    if current_status == "awaiting_approval":

        st.warning(
            "This analysis is ready for human review."
        )

        review_notes = st.text_area(
            "Review Notes",
            placeholder=(
                "Add approval notes or describe "
                "what needs to be changed..."
            ),
            key=f"review_notes_{job_id}",
        )

        col1, col2, col3 = st.columns(3)

        # Approve
        with col1:

            if st.button(
                "Approve",
                type="primary",
                use_container_width=True,
                key=f"approve_{job_id}",
            ):

                try:

                    _approve_job(
                        job_id,
                        "approved",
                        review_notes,
                        access_token,
                    )

                    st.success(
                        "Job approved successfully."
                    )

                    time.sleep(0.5)
                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Approval failed: {e}"
                    )

        # Needs Revision
        with col2:

            if st.button(
                "Needs Revision",
                use_container_width=True,
                key=f"revision_{job_id}",
            ):

                if not review_notes.strip():

                    st.warning(
                        "Please provide revision notes "
                        "before requesting changes."
                    )

                else:

                    try:

                        _approve_job(
                            job_id,
                            "needs_revision",
                            review_notes,
                            access_token,
                        )

                        st.success(
                            "Revision requested. "
                            "The job has been queued "
                            "for reprocessing."
                        )

                        time.sleep(0.5)
                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"Revision request failed: {e}"
                        )

        # Reject
        with col3:

            if st.button(
                "❌ Reject",
                use_container_width=True,
                key=f"reject_{job_id}",
            ):

                try:

                    _approve_job(
                        job_id,
                        "rejected",
                        review_notes,
                        access_token,
                    )

                    st.success(
                        "Job rejected."
                    )

                    time.sleep(0.5)
                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Rejection failed: {e}"
                    )

    # -----------------------------------------------------
    # Needs Revision
    # -----------------------------------------------------

    elif current_status == "needs_revision":

        st.warning(
            "This job has been marked for revision."
        )

        human_notes = _get_field(
            job_data,
            ["human_notes"],
        )

        if human_notes:

            st.markdown(
                "**Previous Review Feedback:**"
            )

            st.info(
                human_notes
            )

        st.markdown(
            "Click **Reprocess Revision** to run "
            "the analysis again using the review feedback."
        )

        if st.button(
            "Reprocess Revision",
            type="primary",
            use_container_width=True,
            key=f"reprocess_{job_id}",
        ):

            try:

                _reprocess_job(
                    job_id,
                    access_token,
                )

                st.success(
                    "Revision has been queued "
                    "for reprocessing."
                )

                time.sleep(0.5)
                st.rerun()

            except Exception as e:

                st.error(
                    f"Reprocessing failed: {e}"
                )

    # -----------------------------------------------------
    # Approved
    # -----------------------------------------------------

    elif current_status == "approved":

        st.success(
            "This analysis has been approved."
        )

        human_notes = _get_field(
            job_data,
            ["human_notes"],
        )

        if human_notes:

            st.markdown(
                "**Review Notes:**"
            )

            st.write(
                human_notes
            )

    # -----------------------------------------------------
    # Rejected
    # -----------------------------------------------------

    elif current_status == "rejected":

        st.error(
            "This analysis has been rejected."
        )

        human_notes = _get_field(
            job_data,
            ["human_notes"],
        )

        if human_notes:

            st.markdown(
                "**Review Notes:**"
            )

            st.write(
                human_notes
            )

    # -----------------------------------------------------
    # Processing
    # -----------------------------------------------------

    elif current_status in (
        "queued",
        "running",
    ):

        st.info(
            "The analysis is currently being processed. "
            "Human review will be available once "
            "processing is complete."
        )

    # -----------------------------------------------------
    # Failed
    # -----------------------------------------------------

    elif current_status == "failed":

        error = _get_field(
            job_data,
            ["error"],
        )

        st.error(
            "The analysis failed."
        )

        if error:

            st.code(
                error
            )


# =========================================================
# Main Job Details Page
# =========================================================

def show_job_details(
    job_id: str,
    access_token: str | None = None,
):
    """Main Job Details page."""

    # =====================================================
    # Authentication
    # =====================================================

    if not access_token:

        access_token = _get_access_token()

    if not access_token:

        st.error(
            "Authentication token not found. "
            "Please log in again."
        )

        return

    # =====================================================
    # Page Header
    # =====================================================

    st.title(" Job Details")

    if not job_id:

        st.warning(
            "No job has been selected."
        )

        return

    # =====================================================
    # Back Button
    # =====================================================

    if st.button(
        "← Back to Jobs",
        key=f"back_jobs_{job_id}",
    ):

        st.session_state["page"] = "jobs"
        st.rerun()

    st.divider()

    # =====================================================
    # Fetch Job
    # =====================================================

    try:

        job_data = _get_job_status(
            job_id,
            access_token,
        )

    except Exception as e:

        st.error(
            f"Unable to load job details: {e}"
        )

        return

    
    # =====================================================
    # Validate Response
    # =====================================================

    if not job_data:

        st.warning(
            "No job information was returned."
        )

        return

    # =====================================================
    # Job Header
    # =====================================================

    job_question = _get_field(
        job_data,
        ["question"],
        "Analysis",
    )

    st.header(
        job_question
    )

    status = job_data.get(
        "status",
        "unknown",
    )

    _display_status(
        status
    )

    # =====================================================
    # Job Information
    # =====================================================

    with st.expander(
        "Job Information",
        expanded=False,
    ):

        st.write(
            f"**Job ID:** `{job_id}`"
        )

        created_at = _get_field(
            job_data,
            ["created_at"],
        )

        if created_at:

            st.write(
                f"**Created:** {created_at}"
            )

        updated_at = _get_field(
            job_data,
            ["updated_at"],
        )

        if updated_at:

            st.write(
                f"**Updated:** {updated_at}"
            )

        revision_count = _get_field(
            job_data,
            ["revision_count"],
        )

        if revision_count is not None:

            st.write(
                f"**Revision Count:** "
                f"{revision_count}"
            )

    # =====================================================
    # Error
    # =====================================================

    if status == "failed":

        error = _get_field(
            job_data,
            ["error"],
        )

        if error:

            st.error(
                "Pipeline Error"
            )

            st.code(
                error
            )

    # =====================================================
    # Dataset Information
    # =====================================================

    _display_dataset_information(
        job_data
    )

    st.divider()

    # =====================================================
    # Report
    # =====================================================

    _display_report(
        job_data
    )

    st.divider()

    # =====================================================
    # Visualizations
    # =====================================================

    _display_visualizations(
        job_id,
        job_data,
        access_token,
    )

    st.divider()

    # =====================================================
    # Agent Decisions
    # =====================================================

    _display_explanations(
        job_data
    )

    st.divider()

    # =====================================================
    # Critique
    # =====================================================

    _display_critique(
        job_data
    )

    st.divider()

    # =====================================================
    # Previous Human Review
    # =====================================================

    _display_human_review_history(
        job_data
    )

    # =====================================================
    # Human Approval / Revision
    # =====================================================

    st.divider()

    _display_human_approval(
        job_id,
        job_data,
        access_token,
    )

    # =====================================================
    # Auto Refresh
    # =====================================================

    if status in (
        "queued",
        "running",
    ):

        st.divider()

        st.info(
            "This page will refresh automatically "
            "while the job is processing."
        )

        time.sleep(3)
        st.rerun()