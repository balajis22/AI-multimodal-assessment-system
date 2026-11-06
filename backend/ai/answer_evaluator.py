from backend.ai.question_bank import get_question
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re


# --------------------------------------------------
# Load semantic model ONCE
# --------------------------------------------------

print("Loading semantic evaluation model...")

model = SentenceTransformer("all-MiniLM-L6-v2")

print("Semantic model loaded!")


# --------------------------------------------------
# Utility: convert similarity to 0-100
# --------------------------------------------------

def similarity_to_score(similarity):
    """
    Convert cosine similarity into a safe 0-100 score.
    """

    similarity = max(0.0, min(1.0, float(similarity)))

    return round(similarity * 100)


# --------------------------------------------------
# Semantic similarity
# --------------------------------------------------

def semantic_similarity(text1, text2):
    """
    Calculate semantic similarity between two texts.
    """

    if not text1 or not text2:
        return 0.0

    embeddings = model.encode(
        [text1, text2],
        normalize_embeddings=True
    )

    similarity = cosine_similarity(
        [embeddings[0]],
        [embeddings[1]]
    )[0][0]

    return float(similarity)


# --------------------------------------------------
# Split answer into sentences
# --------------------------------------------------

def split_sentences(text):
    """
    Split an answer into individual sentences.
    """

    sentences = re.split(
        r"[.!?]+",
        text
    )

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


# --------------------------------------------------
# Concept coverage
# --------------------------------------------------
def concept_coverage(answer, expected_concepts):
    """
    Evaluate whether the candidate actually demonstrates
    each expected concept.

    Evidence phrases provide explicit concept evidence.
    Semantic similarity helps recognize paraphrases.
    """

    if not answer or not answer.strip():
        return {
            "coverage_score": 0,
            "concept_scores": {}
        }

    answer_lower = answer.lower()

    sentences = split_sentences(answer)

    if not sentences:
        return {
            "coverage_score": 0,
            "concept_scores": {}
        }

    sentence_embeddings = model.encode(
        sentences,
        normalize_embeddings=True
    )

    concept_scores = {}

    # Semantic threshold used only as supporting evidence
    SEMANTIC_THRESHOLD = 0.50

    for concept in expected_concepts:

        name = concept["name"]
        aliases = concept["aliases"]
        evidence = concept.get("evidence", [])

        # ------------------------------------------
        # STEP 1: Explicit evidence
        # ------------------------------------------

        explicit_match = False

        for phrase in evidence:

            if phrase.lower() in answer_lower:
                explicit_match = True
                break

        if explicit_match:
            concept_scores[name] = 100
            continue

        # ------------------------------------------
        # STEP 2: Semantic paraphrase matching
        # ------------------------------------------

        phrases = [name] + aliases

        best_similarity = 0.0

        for phrase in phrases:

            phrase_embedding = model.encode(
                [phrase],
                normalize_embeddings=True
            )

            similarities = cosine_similarity(
                phrase_embedding,
                sentence_embeddings
            )[0]

            best_similarity = max(
                best_similarity,
                max(similarities)
            )

        # ------------------------------------------
        # STEP 3: Partial semantic evidence
        # ------------------------------------------

        if best_similarity >= SEMANTIC_THRESHOLD:

            score = similarity_to_score(
                best_similarity
            )

            # Don't allow semantic-only matching
            # to look like perfect explicit evidence.
            score = min(score, 70)

        else:

            score = 0

        concept_scores[name] = score

    # ------------------------------------------
    # Overall concept coverage
    # ------------------------------------------

    if concept_scores:

        coverage_score = round(
            sum(concept_scores.values())
            / len(concept_scores)
        )

    else:

        coverage_score = 0

    return {
        "coverage_score": coverage_score,
        "concept_scores": concept_scores
    }

# --------------------------------------------------
# Complete answer evaluation
# --------------------------------------------------

def evaluate_answer(
    question,
    answer,
    expected_concepts
):
    """
    Evaluate a candidate's interview answer.

    Metrics:

    1. Semantic relevance
    2. Concept coverage
    3. Final answer score
    """

    if not answer or not answer.strip():

        return {
            "semantic_score": 0,
            "concept_coverage": 0,
            "concept_scores": {},
            "answer_score": 0,
            "feedback": "No answer was detected."
        }

    # ----------------------------------------------
    # Question-answer relevance
    # ----------------------------------------------

    semantic_score = similarity_to_score(
        semantic_similarity(
            question,
            answer
        )
    )

    # ----------------------------------------------
    # Concept coverage
    # ----------------------------------------------

    coverage = concept_coverage(
        answer,
        expected_concepts
    )

    coverage_score = coverage[
        "coverage_score"
    ]

    # ----------------------------------------------
    # Final score
    # ----------------------------------------------

    answer_score = round(
        semantic_score * 0.40
        +
        coverage_score * 0.60
    )

    # Safety
    answer_score = max(
        0,
        min(100, answer_score)
    )

    # ----------------------------------------------
    # Feedback
    # ----------------------------------------------

    if answer_score >= 85:

        feedback = (
            "Excellent answer. You addressed "
            "the question clearly and covered "
            "the key concepts."
        )

    elif answer_score >= 70:

        feedback = (
            "Good answer. You addressed the "
            "main idea, but some important "
            "concepts could be explained "
            "in more detail."
        )

    elif answer_score >= 50:

        feedback = (
            "Partially relevant answer. "
            "Try to explain the key concepts "
            "more directly."
        )

    else:

        feedback = (
            "The answer needs improvement. "
            "Focus on the concepts specifically "
            "asked in the question."
        )

    return {

        "semantic_score": semantic_score,

        "concept_coverage": coverage_score,

        "concept_scores": coverage[
            "concept_scores"
        ],

        "answer_score": answer_score,

        "feedback": feedback
    }


# --------------------------------------------------
# Test
# --------------------------------------------------

# --------------------------------------------------
# Test
# --------------------------------------------------

if __name__ == "__main__":

    from backend.ai.question_bank import get_question

    question_data = get_question(
        "Machine Learning Engineer",
        2
    )

    question = question_data["question"]
    expected_concepts = question_data["concepts"]

    answers = [

        (
            "Overfitting happens when a model performs "
            "very well on the training data but does not "
            "generalize to unseen data. We can reduce it "
            "using regularization, cross validation, or "
            "more training data."
        ),

        (
            "Overfitting means the model learns "
            "the training data very closely."
        ),

        (
            "Python is a programming language "
            "used for developing software applications."
        )
    ]

    print("\n")
    print("=" * 60)
    print("SEMANTIC + CONCEPT ANSWER EVALUATION")
    print("=" * 60)

    for i, answer in enumerate(
        answers,
        start=1
    ):

        result = evaluate_answer(
            question,
            answer,
            expected_concepts
        )

        print("\n")
        print(f"ANSWER {i}")
        print("-" * 60)

        print(answer)

        print("\nSemantic Relevance:")

        print(
            f"{result['semantic_score']}/100"
        )

        print("\nConcept Coverage:")

        print(
            f"{result['concept_coverage']}/100"
        )

        print("\nIndividual Concepts:")

        for concept, score in result[
            "concept_scores"
        ].items():

            print(
                f"  {score:>3}/100  {concept}"
            )

        print("\nFinal Answer Score:")

        print(
            f"{result['answer_score']}/100"
        )

        print("\nFeedback:")

        print(
            result["feedback"]
        )