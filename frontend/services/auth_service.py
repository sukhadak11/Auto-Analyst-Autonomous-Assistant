import requests

from services.api_client import API_URL


def login_user(email, password):
    try:
        response = requests.post(
            f"{API_URL}/auth/login",
            json={
                "email": email,
                "password": password,
            },
            timeout=10,
        )

        if response.status_code == 200:
            return response.json(), None

        try:
            error = response.json().get(
                "detail",
                "Login failed."
            )
        except Exception:
            error = "Login failed."

        return None, error

    except requests.exceptions.ConnectionError:
        return None, (
            "Unable to connect to the AutoAnalyst API. "
            "Make sure FastAPI is running on port 8001."
        )

    except requests.exceptions.Timeout:
        return None, "The authentication request timed out."

    except requests.exceptions.RequestException as e:
        return None, f"Login failed: {str(e)}"


def register_user(email, password):
    try:
        response = requests.post(
            f"{API_URL}/auth/register",
            json={
                "email": email,
                "password": password,
            },
            timeout=10,
        )

        if response.status_code == 200:
            return response.json(), None

        try:
            error = response.json().get(
                "detail",
                "Registration failed."
            )
        except Exception:
            error = "Registration failed."

        return None, error

    except requests.exceptions.ConnectionError:
        return None, (
            "Unable to connect to the AutoAnalyst API. "
            "Make sure FastAPI is running on port 8001."
        )

    except requests.exceptions.Timeout:
        return None, "The registration request timed out."

    except requests.exceptions.RequestException as e:
        return None, f"Registration failed: {str(e)}"