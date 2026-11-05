# AI-Powered Multimodal Interview and Personality Assessment System

## Team

- Yashica G
- Balaji S
- Nidhi Mishra
- Gagan K

## Guide

Mr. Saurav Kumar Topo

---

## Overview

This project aims to build an AI-powered interview assessment system that analyzes candidates using multiple modalities:

- Facial Emotion Recognition
- Speech Emotion Recognition
- NLP-based Text Analysis

The outputs from these modules are combined using multimodal fusion to generate:

- Confidence Score
- Communication Score
- Emotional Stability Score
- Interview Readiness Score

---

## Technologies

- Python
- OpenCV
- MediaPipe
- TensorFlow
- Hugging Face
- Librosa
- Whisper
- Streamlit

---

## Deployment

This project includes a repository-root `streamlit_app.py` entrypoint so it can be deployed directly on Streamlit Community Cloud. The app can also be started with:

```bash
streamlit run streamlit_app.py
```

The Streamlit app runs TensorFlow, MediaPipe, and YAMNet. Whisper transcription and Sentence Transformers scoring run in the separate Docker service in `whisper_service/`, keeping PyTorch out of the TensorFlow process. Deploy that service and configure `ai_service_url` and `ai_service_token` in Streamlit Cloud secrets as described in [`whisper_service/README.md`](whisper_service/README.md).

For Streamlit Community Cloud, select Python 3.12 in Advanced settings when creating the app; the TensorFlow version in this repository does not support the Python 3.14 environment shown in the earlier deployment logs. Community Cloud does not let you change an existing app's Python version; delete and redeploy it to select another version. Add Firebase configuration in Streamlit secrets using the `firebase.api_key` key if Firebase authentication is enabled.

## Status

🚧 Under Development
