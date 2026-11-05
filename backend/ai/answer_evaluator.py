import re


def _tokens(text):
    return {word for word in re.findall(r"[a-z0-9]+", text.lower()) if len(word) > 2}


def evaluate_answer(question, answer, expected_concepts):
    """Lightweight keyword scoring; transformer semantic scoring is disabled."""
    answer = (answer or "").strip()
    if not answer:
        return {
            "semantic_score": 0,
            "concept_coverage": 0,
            "concept_scores": {},
            "answer_score": 0,
            "feedback": "No answer was transcribed. Speech transcription is disabled in this deployment.",
        }

    answer_lower = answer.lower()
    answer_tokens = _tokens(answer)
    question_tokens = _tokens(question or "")
    overlap = len(answer_tokens & question_tokens) / max(1, len(question_tokens))
    relevance_score = round(min(1.0, overlap) * 100)

    concept_scores = {}
    for concept in expected_concepts or []:
        name = concept.get("name", "Concept")
        phrases = [name, *concept.get("aliases", []), *concept.get("evidence", [])]
        matched = any(str(phrase).lower() in answer_lower for phrase in phrases if phrase)
        concept_scores[name] = 100 if matched else 0

    coverage = round(sum(concept_scores.values()) / len(concept_scores)) if concept_scores else 0
    answer_score = round(relevance_score * 0.4 + coverage * 0.6)
    if answer_score >= 85:
        feedback = "Good keyword match. Review the answer for completeness."
    elif answer_score >= 50:
        feedback = "Some expected keywords were found. Explain the key concepts more directly."
    else:
        feedback = "Few expected keywords were found. Address the question's key concepts."

    return {
        "semantic_score": relevance_score,
        "concept_coverage": coverage,
        "concept_scores": concept_scores,
        "answer_score": answer_score,
        "feedback": feedback,
    }
