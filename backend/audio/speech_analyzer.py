import whisper
import tensorflow_hub as hub
import librosa
import numpy as np
import sounddevice as sd
import re

from scipy.io.wavfile import write


# --------------------------------------------------
# Load models ONCE
# --------------------------------------------------

print("Loading Whisper...")
whisper_model = whisper.load_model("base")

print("Loading YAMNet...")
yamnet = hub.load("https://tfhub.dev/google/yamnet/1")

class_map = yamnet.class_map_path().numpy().decode("utf-8")

with open(class_map) as f:
    labels = [
        line.strip().split(",")[2]
        for line in f.readlines()[1:]
    ]

print("Audio models loaded successfully!\n")


# --------------------------------------------------
# Record + Transcribe
# --------------------------------------------------

def record_and_transcribe(
    seconds=10,
    filename="sample.wav"
):
    """
    Record the candidate's answer and convert
    the speech into text using Whisper.

    Returns:
        transcript
    """

    fs = 16000

    

    print("Speak now...")

    recording = sd.rec(
        int(seconds * fs),
        samplerate=fs,
        channels=1,
        dtype="int16"
    )

    sd.wait()

    write(
        filename,
        fs,
        recording
    )

    print("Recording complete!")

    # ----------------------------------------------
    # Whisper transcription
    # ----------------------------------------------

    result = whisper_model.transcribe(
        filename
    )

    transcript = result["text"].strip()

    return transcript


# --------------------------------------------------
# Full Speech Analysis
# --------------------------------------------------

def analyze_speech(seconds=10, start_event=None):

    fs = 16000

   

   
    if start_event is not None:
        start_event.wait()

    print("Speak now...")

    recording = sd.rec(
        int(seconds * fs),
        samplerate=fs,
        channels=1,
        dtype="int16"
    )

    sd.wait()

    write(
        "sample.wav",
        fs,
        recording
    )

    print("Recording complete!")

    # Convert in-memory int16 audio to normalized float32 for Whisper (no ffmpeg needed)
    audio_float = recording.flatten().astype(np.float32) / 32768.0

    result = whisper_model.transcribe(
        audio_float
    )

    transcript = result["text"]

    # ----------------------------------------------
    # Fillers
    # ----------------------------------------------

    fillers = [
        "um",
        "uh",
        "like",
        "actually",
        "basically",
        "you know",
        "sort of",
        "kind of",
        "so"
    ]

    text = transcript.lower()

    total_fillers = 0

    filler_counts = {}

    for filler in fillers:

        count = len(
            re.findall(
                r"\b"
                + re.escape(filler)
                + r"\b",
                text
            )
        )

        filler_counts[filler] = count

        total_fillers += count

    # ----------------------------------------------
    # WPM
    # ----------------------------------------------

    word_count = len(
        text.split()
    )

    wpm = round(
        word_count / (seconds / 60)
    )

    # ----------------------------------------------
    # Sound Classification
    # ----------------------------------------------

    waveform, sr = librosa.load(
        "sample.wav",
        sr=16000
    )

    scores, embeddings, spectrogram = yamnet(
        waveform
    )

    scores = scores.numpy()

    mean_scores = np.mean(
        scores,
        axis=0
    )

    idx = np.argmax(
        mean_scores
    )

    sound = labels[idx]

    confidence = float(
        mean_scores[idx]
    )

    NATURAL = [
        "Rain",
        "Thunder",
        "Wind",
        "Water",
        "Ocean",
        "Bird",
        "Stream"
    ]

    natural = any(
        x.lower() in sound.lower()
        for x in NATURAL
    )

    # ----------------------------------------------
    # Speech Score
    # ----------------------------------------------

    speech_score = 100

    speech_score -= (
        total_fillers * 3
    )

    if wpm < 90:

        speech_score -= 10

    elif wpm > 170:

        speech_score -= 10

    speech_score = max(
        0,
        speech_score
    )

    # ----------------------------------------------
    # Return Everything
    # ----------------------------------------------

    return {

        "transcript": transcript,

        "fillers": filler_counts,

        "total_fillers": total_fillers,

        "word_count": word_count,

        "wpm": wpm,

        "background": sound,

        "background_confidence": confidence,

        "background_natural": natural,

        "speech_score": speech_score
    }


# --------------------------------------------------
# Test
# --------------------------------------------------

if __name__ == "__main__":

    transcript = record_and_transcribe(
        seconds=10
    )

    print("\n========== TRANSCRIPT ==========\n")

    print(transcript)