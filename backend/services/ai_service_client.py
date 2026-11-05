"""Client for the separately deployed Whisper and semantic NLP service."""

import os

import requests
import streamlit as st


def _configuration():
    url = os.getenv("AI_SERVICE_URL", "").rstrip("/")
    token = os.getenv("AI_SERVICE_TOKEN", "")
    try:
        url = url or str(st.secrets.get("ai_service_url", "")).rstrip("/")
        token = token or str(st.secrets.get("ai_service_token", ""))
    except Exception:
        pass
    if not url or not token:
        raise RuntimeError(
            "AI backend is not configured. Set ai_service_url and ai_service_token "
            "in Streamlit secrets."
        )
    return url, token


def _post(path, **kwargs):
    url, token = _configuration()
    response = requests.post(
        f"{url}{path}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=300,
        **kwargs,
    )
    response.raise_for_status()
    return response.json()


def transcribe_file(filename):
    with open(filename, "rb") as audio_file:
        result = _post(
            "/transcribe",
            files={"file": (os.path.basename(filename), audio_file, "audio/wav")},
        )
    return result["transcript"]


def evaluate_answer(question, answer, expected_concepts):
    return _post(
        "/evaluate",
        json={
            "question": question,
            "answer": answer,
            "expected_concepts": expected_concepts or [],
        },
    )
