import requests
import streamlit as st

API_URL = "http://localhost:8001"


def get_auth_headers():
    token = st.session_state.get("access_token")

    if not token:
        return {}

    return {
        "Authorization": f"Bearer {token}"
    }


def handle_response(response):
    if response.status_code == 401:
        st.session_state.authenticated = False
        st.session_state.access_token = None
        st.session_state.user_email = ""
        st.session_state.user_role = "user"

        return None, "Your session has expired. Please log in again."

    if response.status_code >= 400:
        try:
            detail = response.json().get(
                "detail",
                "An API error occurred."
            )
        except Exception:
            detail = "An API error occurred."

        return None, detail

    try:
        return response.json(), None
    except Exception:
        return None, None