import requests
import streamlit as st


API_BASE_URL = "http://127.0.0.1:8001"


# ============================================================
# Authentication Headers
# ============================================================

def get_headers(access_token: str | None = None):
    """
    Return Authorization headers for API requests.
    """

    if not access_token:
        access_token = st.session_state.get("access_token")

    if not access_token:
        return {}

    return {
        "Authorization": f"Bearer {access_token}"
    }


# ============================================================
# Jobs
# ============================================================

def fetch_jobs(access_token: str | None = None):
    """
    Fetch jobs for the currently logged-in user.

    Admin users receive all jobs from the backend.
    Normal users receive only their own jobs.
    """

    if not access_token:
        access_token = st.session_state.get("access_token")

    if not access_token:
        return [], "Authentication token not found."

    try:
        response = requests.get(
            f"{API_BASE_URL}/jobs",
            headers=get_headers(access_token),
            timeout=30,
        )

        if response.status_code != 200:
            try:
                detail = response.json().get(
                    "detail",
                    "Failed to fetch jobs."
                )
            except Exception:
                detail = response.text or "Failed to fetch jobs."

            return [], detail

        data = response.json()

        # Backend returns a list
        if isinstance(data, list):
            return data, None

        # Support {"jobs": [...]}
        if isinstance(data, dict):
            jobs = data.get("jobs")

            if jobs is not None:
                return jobs, None

        return [], "Unexpected response from the server."

    except requests.RequestException as e:
        return [], f"Unable to connect to API: {e}"


# ============================================================
# Reports
# ============================================================

def fetch_reports(access_token: str | None = None):
    """
    Fetch completed analysis reports.

    Admin users receive all reports.
    Normal users receive only their own reports.
    """

    if not access_token:
        access_token = st.session_state.get("access_token")

    if not access_token:
        return [], "Authentication token not found."

    try:
        response = requests.get(
            f"{API_BASE_URL}/reports",
            headers=get_headers(access_token),
            timeout=30,
        )

        if response.status_code != 200:
            try:
                detail = response.json().get(
                    "detail",
                    "Failed to fetch reports."
                )
            except Exception:
                detail = response.text or "Failed to fetch reports."

            return [], detail

        data = response.json()

        # Backend returns a list
        if isinstance(data, list):
            return data, None

        # Support {"reports": [...]}
        if isinstance(data, dict):
            reports = data.get("reports")

            if reports is not None:
                return reports, None

        return [], "Unexpected response from the server."

    except requests.RequestException as e:
        return [], f"Unable to connect to API: {e}"


# ============================================================
# Job Status
# ============================================================

def get_job_status(
    job_id: str,
    access_token: str | None = None
):
    """
    Fetch the current status and result of a job.
    """

    if not access_token:
        access_token = st.session_state.get("access_token")

    if not access_token:
        raise Exception("Authentication token not found.")

    try:
        response = requests.get(
            f"{API_BASE_URL}/status/{job_id}",
            headers=get_headers(access_token),
            timeout=30,
        )

        if response.status_code != 200:
            try:
                detail = response.json().get(
                    "detail",
                    "Failed to fetch job status."
                )
            except Exception:
                detail = response.text or "Failed to fetch job status."

            raise Exception(detail)

        return response.json()

    except requests.RequestException as e:
        raise Exception(
            f"Unable to connect to API: {e}"
        )


# ============================================================
# Human Approval / Review
# ============================================================

def approve_job(
    job_id: str,
    decision: str,
    notes: str | None = None,
    access_token: str | None = None
):
    """
    Submit human review decision for a job.

    Supported decisions:
        - approved
        - rejected
        - needs_revision
    """

    if not access_token:
        access_token = st.session_state.get("access_token")

    if not access_token:
        raise Exception("Authentication token not found.")

    try:
        response = requests.post(
            f"{API_BASE_URL}/approve/{job_id}",
            headers=get_headers(access_token),
            json={
                "decision": decision,
                "notes": notes,
            },
            timeout=30,
        )

        if response.status_code != 200:
            try:
                detail = response.json().get(
                    "detail",
                    "Failed to review job."
                )
            except Exception:
                detail = response.text or "Failed to review job."

            raise Exception(detail)

        return response.json()

    except requests.RequestException as e:
        raise Exception(
            f"Unable to connect to API: {e}"
        )


# ============================================================
# Reprocess Job
# ============================================================

def reprocess_job(
    job_id: str,
    access_token: str | None = None
):
    """
    Reprocess a job after human revision feedback.
    """

    if not access_token:
        access_token = st.session_state.get("access_token")

    if not access_token:
        raise Exception("Authentication token not found.")

    try:
        response = requests.post(
            f"{API_BASE_URL}/reprocess/{job_id}",
            headers=get_headers(access_token),
            timeout=30,
        )

        if response.status_code != 200:
            try:
                detail = response.json().get(
                    "detail",
                    "Failed to reprocess job."
                )
            except Exception:
                detail = response.text or "Failed to reprocess job."

            raise Exception(detail)

        return response.json()

    except requests.RequestException as e:
        raise Exception(
            f"Unable to connect to API: {e}"
        )