import requests
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

FIREBASE_URL = "https://identitytoolkit.googleapis.com/v1/accounts"


class FirebaseAuthError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def _get_api_key():
    try:
        api_key = st.secrets["firebase"]["api_key"]
    except (KeyError, StreamlitSecretNotFoundError) as exc:
        raise FirebaseAuthError(
            "CONFIGURATION_ERROR",
            "Firebase configuration is missing. Add "
            "[firebase] api_key to .streamlit/secrets.toml.",
        ) from exc

    if (
        not isinstance(api_key, str)
        or not api_key.strip()
        or api_key.strip() == "YOUR_FIREBASE_WEB_API_KEY"
    ):
        raise FirebaseAuthError(
            "CONFIGURATION_ERROR",
            "Firebase configuration is invalid. Set a valid "
            "firebase.api_key in .streamlit/secrets.toml.",
        )

    return api_key.strip()


def _firebase_request(endpoint, payload):
    try:
        response = requests.post(
            f"{FIREBASE_URL}:{endpoint}",
            params={"key": _get_api_key()},
            json=payload,
            timeout=15,
        )
    except requests.RequestException as exc:
        raise FirebaseAuthError(
            "NETWORK_ERROR",
            "Cannot connect to Firebase. Check your internet connection.",
        ) from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise FirebaseAuthError(
            "INVALID_RESPONSE",
            "Firebase returned an invalid response.",
        ) from exc

    if not isinstance(data, dict):
        raise FirebaseAuthError(
            "INVALID_RESPONSE",
            "Firebase returned an invalid response.",
        )

    if not response.ok:
        error = data.get("error", {})
        error_code = error.get("message", "") if isinstance(error, dict) else ""
        messages = {
            "EMAIL_EXISTS": "This email is already registered.",
            "EMAIL_NOT_FOUND": "No account found. Please create a new account.",
            "INVALID_EMAIL": "Enter a valid email address.",
            "INVALID_LOGIN_CREDENTIALS":
                "Invalid email/username or password. Please try again.",
            "INVALID_PASSWORD":
                "Invalid email/username or password. Please try again.",
            "USER_DISABLED": "This account has been disabled.",
            "WEAK_PASSWORD": "Choose a stronger password.",
            "TOO_MANY_ATTEMPTS_TRY_LATER":
                "Too many attempts. Please try again later.",
            "API_KEY_INVALID": "Check your Firebase Web API key.",
            "INVALID_API_KEY": "Check your Firebase Web API key.",
            "API_KEY_SERVICE_BLOCKED":
                "Firebase Authentication is blocked for this API key.",
            "CONFIGURATION_NOT_FOUND":
                "Enable Email/Password in Firebase Authentication.",
            "PROJECT_NOT_FOUND":
                "Check that the Firebase Web API key belongs to your project.",
            "OPERATION_NOT_ALLOWED":
                "Enable Email/Password in Firebase Authentication.",
        }

        if error_code.startswith("WEAK_PASSWORD"):
            message = "Use a password of at least 6 characters."
        else:
            message = messages.get(
                error_code,
                "Authentication failed. Please try again.",
            )

        raise FirebaseAuthError(error_code or "AUTHENTICATION_ERROR", message)

    return data


def _authenticate(endpoint, email, password, display_name=None):
    payload = {
        "email": email.strip(),
        "password": password,
        "returnSecureToken": True,
    }

    if display_name:
        payload["displayName"] = display_name.strip()

    data = _firebase_request(endpoint, payload)
    required_fields = ("localId", "email", "idToken", "refreshToken")
    if any(
        not isinstance(data.get(field), str) or not data[field]
        for field in required_fields
    ):
        raise FirebaseAuthError(
            "INVALID_RESPONSE",
            "Firebase did not return complete account details.",
        )

    return data


def register_user(name, email, password):
    return _authenticate(
        "signUp",
        email,
        password,
        display_name=name,
    )


def login_user(email, password):
    return _authenticate(
        "signInWithPassword",
        email,
        password,
    )


def get_user_profile(id_token, expected_uid):
    data = _firebase_request("lookup", {"idToken": id_token})
    users = data.get("users")

    if not isinstance(users, list):
        raise FirebaseAuthError(
            "PROFILE_NOT_FOUND",
            "Firebase did not return the signed-in user's profile.",
        )

    profile = next(
        (
            user for user in users
            if isinstance(user, dict) and user.get("localId") == expected_uid
        ),
        None,
    )
    if profile is None:
        raise FirebaseAuthError(
            "PROFILE_MISMATCH",
            "The signed-in user's profile could not be verified.",
        )

    return profile
