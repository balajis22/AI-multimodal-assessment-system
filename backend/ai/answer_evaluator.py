from backend.services.ai_service_client import evaluate_answer as _evaluate_remote


def evaluate_answer(question, answer, expected_concepts):
    """Use the separately deployed Sentence Transformers inference service."""
    return _evaluate_remote(question, answer, expected_concepts)
