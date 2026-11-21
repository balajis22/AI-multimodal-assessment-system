def main():
    from backend.vision.interview_analyzer import analyze_interview
    from backend.audio.speech_analyzer import analyze_speech
    from backend.scoring.scoring_engine import InterviewScorer

    print("=" * 60)
    print("        AI INTERVIEW ASSESSMENT SYSTEM")
    print("=" * 60)

    input("\nPress ENTER to start the interview...")

    print("\nInterview Started!")
    print("Answer naturally for the next 20 seconds.\n")

    # -----------------------------------
    # Vision Analysis
    # -----------------------------------

    print("Starting Vision Analysis...\n")

    vision = analyze_interview(duration=20)

    # -----------------------------------
    # Audio Analysis
    # -----------------------------------

    print("\nStarting Speech Analysis...\n")

    audio = analyze_speech(seconds=20)

    # -----------------------------------
    # Scoring
    # -----------------------------------

    scorer = InterviewScorer()

    scorer.emotion_score(
        vision["emotion"]
    )

    scorer.eye_score(
        vision["eye"]
    )

    scorer.head_score(
        vision["head"]
    )

    # Convert 0-100 to 0-20
    speech_points = round(
        audio["speech_score"] / 5
    )

    scorer.speech_score(
        speech_points
    )

    scorer.background_score(
        audio["background_natural"]
    )

    overall = scorer.total()

    # -----------------------------------
    # REPORT
    # -----------------------------------

    print("\n")
    print("=" * 60)
    print("             INTERVIEW REPORT")
    print("=" * 60)

    print("\nVISION")

    print(f"Emotion          : {vision['emotion']}")
    print(f"Eye Contact      : {vision['eye']}")
    print(f"Head Pose        : {vision['head']}")

    print("\nAUDIO")

    print(f"Transcript       : {audio['transcript']}")
    print(f"Fillers          : {audio['total_fillers']}")
    print(f"Words            : {audio['word_count']}")
    print(f"WPM              : {audio['wpm']}")
    print(f"Background       : {audio['background']}")
    print(f"Speech Score     : {audio['speech_score']}/100")

    print("\nOVERALL")

    print(f"Interview Score  : {overall}/100")

    print("\nFEEDBACK")

    if overall >= 90:
        print("Excellent interview performance!")
    elif overall >= 75:
        print("Good interview performance.")
    else:
        print("Needs improvement.")

    if audio["total_fillers"] > 3:
        print("- Reduce filler words.")

    if audio["wpm"] > 170:
        print("- Slow down while speaking.")
    elif audio["wpm"] < 90:
        print("- Speak a little faster.")

    if vision["eye"] != "Looking Center":
        print("- Maintain better eye contact.")

    if vision["head"] != "Center":
        print("- Keep your head facing the interviewer.")

    if not audio["background_natural"]:
        print("- Background noise may require review.")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    import sys
    # If Streamlit is running this file instead of streamlit_app.py, redirect seamlessly to the Streamlit app
    if "streamlit" in sys.modules:
        from frontend.app import *  # noqa: F401,F403
    else:
        main()
