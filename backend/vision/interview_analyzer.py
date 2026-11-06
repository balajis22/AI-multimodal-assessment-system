import cv2
import time
from collections import Counter

from backend.vision.emotion_detector import detect_emotion
from backend.vision.eye_contact import detect_eye_contact
from backend.vision.head_pose import detect_head_pose


def analyze_interview(duration=20, start_event=None, frame_callback=None):

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Warning: Could not open native webcam. Providing default vision metrics.")
        if start_event is not None:
            start_event.wait()
        return {
            "emotion": "Neutral",
            "eye": "Looking Center",
            "head": "Center"
        }

    if start_event is not None:
        start_event.wait()

    emotions = []
    eyes = []
    heads = []

    frame_count = 0
    start_time = time.time()

    # Latest predictions shown on screen
    emotion = "No Face"
    eye = "No Face"
    head = "No Face"
    bbox = None

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        frame_count += 1

        # ---------------------------------
        # Analyze every 10th frame only
        # ---------------------------------
        if frame_count % 10 == 0:

            emotion, confidence, bbox = detect_emotion(frame)
            eye = detect_eye_contact(frame)
            head = detect_head_pose(frame)

            emotions.append(emotion)
            eyes.append(eye)
            heads.append(head)

        # ---------------------------------
        # Draw bounding box
        # ---------------------------------
        if bbox:

            x1, y1, x2, y2 = bbox

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

        # ---------------------------------
        # Display latest predictions
        # ---------------------------------
        cv2.putText(
            frame,
            f"Emotion: {emotion}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"Eye: {eye}",
            (20, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"Head: {head}",
            (20, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 200, 255),
            2
        )

        remaining = max(0, int(duration - (time.time() - start_time)))

        cv2.putText(
            frame,
            f"Time Left: {remaining}s",
            (20, 140),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        if frame_callback is not None:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            try:
                frame_callback(rgb_frame)
            except Exception:
                pass
        else:
            cv2.imshow("Interview Analysis", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        # ---------------------------------
        # Stop after duration seconds
        # ---------------------------------
        if time.time() - start_time >= duration:
            break

    cap.release()
    if frame_callback is None:
        cv2.destroyAllWindows()
        cv2.waitKey(1)

    # ---------------------------------
    # Handle edge case
    # ---------------------------------
    if len(emotions) == 0:
        return {
            "emotion": "No Face",
            "eye": "No Face",
            "head": "No Face"
        }

    return {

        "emotion": Counter(emotions).most_common(1)[0][0],

        "eye": Counter(eyes).most_common(1)[0][0],

        "head": Counter(heads).most_common(1)[0][0]

    }


if __name__ == "__main__":

    result = analyze_interview(duration=20)

    print("\nFinal Vision Report")
    print(result)