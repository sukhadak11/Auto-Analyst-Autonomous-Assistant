import requests
import streamlit as st

from services.api_client import API_URL


def get_headers(access_token: str | None = None):
    """
    Return authorization headers for API requests.
    """

    if not access_token:
        access_token = st.session_state.get("access_token")

    if not access_token:
        return {}

    return {
        "Authorization": f"Bearer {access_token}"
    }


def fetch_admin_dashboard(access_token: str | None = None):
    """
    Fetch admin dashboard statistics.
    """

    if not access_token:
        access_token = st.session_state.get("access_token")

    if not access_token:
        return None, "Authentication token not found."

    try:
        response = requests.get(
            f"{API_URL}/admin/dashboard",
            headers=get_headers(access_token),
            timeout=30,
        )

        if response.status_code != 200:
            try:
                detail = response.json().get(
                    "detail",
                    "Failed to fetch admin dashboard."
                )
            except Exception:
                detail = response.text or "Failed to fetch admin dashboard."

            return None, detail

        return response.json(), None

    except requests.exceptions.ConnectionError:
        return None, (
            "Unable to connect to the AutoAnalyst API. "
            "Make sure FastAPI is running on port 8001."
        )

    except requests.exceptions.Timeout:
        return None, "The admin dashboard request timed out."

    except requests.exceptions.RequestException as e:
        return None, f"Failed to fetch admin dashboard: {str(e)}"


def fetch_admin_users(access_token: str | None = None):
    """
    Fetch all users for the admin.
    """

    if not access_token:
        access_token = st.session_state.get("access_token")

    if not access_token:
        return [], "Authentication token not found."

    try:
        response = requests.get(
            f"{API_URL}/admin/users",
            headers=get_headers(access_token),
            timeout=30,
        )

        if response.status_code != 200:
            try:
                detail = response.json().get(
                    "detail",
                    "Failed to fetch users."
                )
            except Exception:
                detail = response.text or "Failed to fetch users."

            return [], detail

        data = response.json()

        if isinstance(data, list):
            return data, None

        return [], "Unexpected response from the server."

    except requests.exceptions.ConnectionError:
        return [], (
            "Unable to connect to the AutoAnalyst API. "
            "Make sure FastAPI is running on port 8001."
        )

    except requests.exceptions.Timeout:
        return [], "The users request timed out."

    except requests.exceptions.RequestException as e:
        return [], f"Failed to fetch users: {str(e)}"


def fetch_admin_jobs(access_token: str | None = None):
    """
    Fetch all jobs for the admin.
    """

    if not access_token:
        access_token = st.session_state.get("access_token")

    if not access_token:
        return [], "Authentication token not found."

    try:
        response = requests.get(
            f"{API_URL}/admin/jobs",
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

        if isinstance(data, list):
            return data, None

        return [], "Unexpected response from the server."

    except requests.exceptions.ConnectionError:
        return [], (
            "Unable to connect to the AutoAnalyst API. "
            "Make sure FastAPI is running on port 8001."
        )

    except requests.exceptions.Timeout:
        return [], "The admin jobs request timed out."

    except requests.exceptions.RequestException as e:
        return [], f"Failed to fetch jobs: {str(e)}"