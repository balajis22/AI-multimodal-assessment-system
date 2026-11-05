import os
import re
import tempfile
from functools import lru_cache

import whisper
from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


app = FastAPI(title="Interview AI service")


def _authorize(authorization):
    expected = os.getenv("AI_SERVICE_TOKEN", "")
    if not expected:
        raise HTTPException(status_code=500, detail="AI_SERVICE_TOKEN is not configured")
    if authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="Unauthorized")


@lru_cache(maxsize=1)
def _whisper_model():
    return whisper.load_model(os.getenv("WHISPER_MODEL", "base"), device="cpu")


@lru_cache(maxsize=1)
def _semantic_model():
    return SentenceTransformer(os.getenv("SENTENCE_MODEL", "all-MiniLM-L6-v2"), device="cpu")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...), authorization: str = Header(default="")):
    _authorize(authorization)
    suffix = os.path.splitext(file.filename or "audio.wav")[1] or ".wav"
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
            temp_path = temp_file.name
            while chunk := await file.read(1024 * 1024):
                temp_file.write(chunk)
        result = _whisper_model().transcribe(temp_path, fp16=False)
        return {"transcript": result.get("text", "").strip()}
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


class EvaluationRequest(BaseModel):
    question: str
    answer: str = ""
    expected_concepts: list[dict] = []


def _sentences(text):
    return [sentence.strip() for sentence in re.split(r"[.!?]+", text) if sentence.strip()]


def _similarity(left, right):
    if not left or not right:
        return 0.0
    embeddings = _semantic_model().encode([left, right], normalize_embeddings=True)
    return float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])


@app.post("/evaluate")
def evaluate(request: EvaluationRequest, authorization: str = Header(default="")):
    _authorize(authorization)
    answer = request.answer.strip()
    if not answer:
        return {
            "semantic_score": 0,
            "concept_coverage": 0,
            "concept_scores": {},
            "answer_score": 0,
            "feedback": "No answer was detected.",
        }

    score = lambda value: round(max(0.0, min(1.0, float(value))) * 100)
    semantic_score = score(_similarity(request.question, answer))
    sentences = _sentences(answer)
    sentence_embeddings = _semantic_model().encode(sentences, normalize_embeddings=True) if sentences else []
    answer_lower = answer.lower()
    concept_scores = {}
    for concept in request.expected_concepts:
        name = str(concept.get("name", "Concept"))
        evidence = concept.get("evidence") or []
        if any(str(phrase).lower() in answer_lower for phrase in evidence):
            concept_scores[name] = 100
            continue
        phrases = [name, *(concept.get("aliases") or [])]
        best = 0.0
        for phrase in phrases:
            if not sentence_embeddings:
                continue
            phrase_embedding = _semantic_model().encode([str(phrase)], normalize_embeddings=True)
            best = max(best, float(cosine_similarity(phrase_embedding, sentence_embeddings)[0].max()))
        concept_scores[name] = min(score(best), 70) if best >= 0.50 else 0

    coverage = round(sum(concept_scores.values()) / len(concept_scores)) if concept_scores else 0
    answer_score = round(semantic_score * 0.4 + coverage * 0.6)
    if answer_score >= 85:
        feedback = "Excellent answer. You addressed the question clearly and covered the key concepts."
    elif answer_score >= 70:
        feedback = "Good answer. You addressed the main idea, but some important concepts could be explained in more detail."
    elif answer_score >= 50:
        feedback = "Partially relevant answer. Try to explain the key concepts more directly."
    else:
        feedback = "The answer needs improvement. Focus on the concepts specifically asked in the question."
    return {
        "semantic_score": semantic_score,
        "concept_coverage": coverage,
        "concept_scores": concept_scores,
        "answer_score": answer_score,
        "feedback": feedback,
    }
