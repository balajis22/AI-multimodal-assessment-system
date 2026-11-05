# Separate Whisper and NLP backend

Deploy this folder as a Docker web service on a host that supports Docker (for example, Render or Google Cloud Run).

1. Set the service's Dockerfile path to `whisper_service/Dockerfile` (build context: repository root) or deploy `whisper_service` as the service root.
2. Add a long random secret environment variable named `AI_SERVICE_TOKEN`.
3. Deploy and wait for the service to become healthy. Its health URL is `/health`.
4. In Streamlit Cloud, add these keys under **App settings → Secrets**:

```toml
ai_service_url = "https://YOUR-AI-SERVICE-URL"
ai_service_token = "the-same-token-as-AI_SERVICE_TOKEN"
```

The first transcription or evaluation request downloads the selected AI models. Set `WHISPER_MODEL` to `base` by default, or `small` if the service has enough memory. You can set `SENTENCE_MODEL` to a compatible Sentence Transformers model; it defaults to `all-MiniLM-L6-v2`.
