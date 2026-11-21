import os
import streamlit.components.v1 as components

# Declare the custom component pointing to this folder
_component_dir = os.path.dirname(os.path.abspath(__file__))
_video_recorder_component = components.declare_component(
    "video_interview_recorder",
    path=_component_dir
)


def video_interview_recorder(duration=20, key=None):
    """
    Renders a live browser webcam & microphone virtual interview recorder.
    Returns None while waiting, or a dictionary when recording completes:
    {
        "video": "data:video/webm;base64,...",
        "audio": "data:audio/wav;base64,...",
        "duration": int
    }
    """
    return _video_recorder_component(duration=duration, key=key, default=None)
