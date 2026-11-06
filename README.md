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

If you are using Streamlit Cloud, connect the repository to GitHub and choose the branch you want to publish. For Firebase authentication, add your configuration in `.streamlit/secrets.toml` using the `firebase.api_key` key.

The deployment dependencies select CPU-only PyTorch so Streamlit Cloud does not download GPU/CUDA runtime packages.

## Status

🚧 Under Development