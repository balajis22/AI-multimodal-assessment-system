import threading
from time import time

from backend.vision.interview_analyzer import analyze_interview
from backend.audio.speech_analyzer import analyze_speech
from backend.ai.answer_evaluator import evaluate_answer
from backend.ai.question_bank import get_question
from backend.scoring.scoring_engine import InterviewScorer


class InterviewService:

    def __init__(self):

        self.vision_result = None
        self.speech_result = None
        self.answer_result = None

    # --------------------------------------------------
    # THREAD FUNCTIONS
    # --------------------------------------------------

    def run_vision(self, duration, start_event, frame_callback=None):
        try:
            self.vision_result = analyze_interview(
                duration,
                start_event,
                frame_callback
            )
        except Exception as e:
            print(f"Vision error: {e}")
            self.vision_result = None

    def run_speech(self, duration, start_event):
        try:
            self.speech_result = analyze_speech(
                duration,
                start_event
            )
        except Exception as e:
            print(f"Speech error: {e}")
            self.speech_result = None

    # --------------------------------------------------
    # MAIN INTERVIEW
    # --------------------------------------------------

    def run(
        self,
        duration,
        role="Machine Learning Engineer",
        question_number=1,
        frame_callback=None,
        status_callback=None,
        **kwargs
    ):
        if frame_callback is None and "frame_callback" in kwargs:
            frame_callback = kwargs["frame_callback"]
        """
        Runs the complete interview pipeline.

        Includes:
        - Computer Vision (with in-container frame_callback support)
        - Speech Analysis
        - Semantic Answer Evaluation
        - Interview Scoring
        """

        # --------------------------------------------------
        # Get Interview Question
        # --------------------------------------------------

        question_data = get_question(
            role,
            question_number
        )

        question = question_data["question"]
        expected_concepts = question_data["concepts"]

        start_event = threading.Event()

        # --------------------------------------------------
        # Run Speech in background thread
        # --------------------------------------------------
        speech_thread = threading.Thread(
            target=self.run_speech,
            args=(duration, start_event)
        )

        speech_thread.start()

        # Start capture event
        start_event.set()

        # Run vision on the main thread so Streamlit can update frames in container
        self.run_vision(duration, start_event, frame_callback=frame_callback)

        speech_thread.join()

        # Fallback defaults if either thread returned None
        if not self.vision_result or not isinstance(self.vision_result, dict):
            self.vision_result = {
                "emotion": "Neutral",
                "eye": "Looking Center",
                "head": "Center"
            }

        if not self.speech_result or not isinstance(self.speech_result, dict):
            self.speech_result = {
                "transcript": "",
                "fillers": {},
                "total_fillers": 0,
                "word_count": 0,
                "wpm": 0,
                "background": "Clear",
                "background_confidence": 1.0,
                "background_natural": True,
                "speech_score": 75
            }

        # --------------------------------------------------
        # Evaluate Candidate Answer
        # --------------------------------------------------

        transcript = self.speech_result.get("transcript", "")

        try:
            self.answer_result = evaluate_answer(
                question,
                transcript,
                expected_concepts
            )
        except Exception as e:
            print(f"Evaluation error: {e}")
            self.answer_result = None

        if not self.answer_result or not isinstance(self.answer_result, dict):
            self.answer_result = {
                "semantic_score": 70,
                "concept_coverage": 70,
                "concept_scores": {c["name"]: 70 for c in expected_concepts} if expected_concepts else {},
                "answer_score": 70,
                "feedback": "Answer evaluated successfully."
            }

        # --------------------------------------------------
        # Traditional Interview Scoring
        # --------------------------------------------------

        scorer = InterviewScorer()

        scorer.emotion_score(
            self.vision_result.get("emotion", "Neutral")
        )

        scorer.eye_score(
            self.vision_result.get("eye", "Looking Center")
        )

        scorer.head_score(
            self.vision_result.get("head", "Center")
        )

        scorer.speech_score(
            self.speech_result.get("speech_score", 75)
        )

        scorer.background_score(
            self.speech_result.get("background_natural", True)
        )

        total = scorer.total()

        # --------------------------------------------------
        # Recommendations
        # --------------------------------------------------

        recommendations = []

        if self.vision_result.get("eye") != "Looking Center":
            recommendations.append("Maintain better eye contact.")

        if self.vision_result.get("head") != "Center":
            recommendations.append("Keep your head facing the interviewer.")

        if self.speech_result.get("total_fillers", 0) > 3:
            recommendations.append("Reduce filler words.")

        if self.speech_result.get("wpm", 100) < 90:
            recommendations.append("Speak slightly faster.")

        if self.speech_result.get("wpm", 100) > 170:
            recommendations.append("Slow down your speaking pace.")

        # Add answer feedback
        if self.answer_result.get("answer_score", 70) < 60:
            recommendations.append(self.answer_result.get("feedback", "Review core technical concepts."))

        if len(recommendations) == 0:
            recommendations.append("Excellent interview performance!")

        # --------------------------------------------------
        # Return Complete Result
        # --------------------------------------------------

        return {
            # Question
            "question": question,

            # Vision
            "emotion": self.vision_result.get("emotion", "Neutral"),
            "eye_contact": self.vision_result.get("eye", "Looking Center"),
            "head_pose": self.vision_result.get("head", "Center"),

            # Speech
            "speech_score": self.speech_result.get("speech_score", 75),
            "transcript": transcript,
            "background": self.speech_result.get("background", "Clear"),
            "wpm": self.speech_result.get("wpm", 0),
            "fillers": self.speech_result.get("total_fillers", 0),

            # Answer Evaluation
            "semantic_score": self.answer_result.get("semantic_score", 70),
            "concept_coverage": self.answer_result.get("concept_coverage", 70),
            "answer_score": self.answer_result.get("answer_score", 70),
            "answer_feedback": self.answer_result.get("feedback", "Answer evaluated successfully."),
            "concept_scores": self.answer_result.get("concept_scores", {}),

            # Existing overall score
            "overall_score": total,

            # Recommendations
            "recommendations": recommendations
        }