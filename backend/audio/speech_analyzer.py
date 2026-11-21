from pathlib import Path
import re
import numpy as np
import sounddevice as sd

from scipy.io.wavfile import write, read as wav_read


# --------------------------------------------------
# Lazy-load models on demand
# --------------------------------------------------

_whisper_model = None


def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        import whisper
        print("Loading Whisper model lazily...")
        _whisper_model = whisper.load_model("base")
        print("Whisper model loaded!")
    return _whisper_model


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

    try:
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
    except Exception as exc:
        print(f"Warning: Native microphone unavailable ({exc}). Using existing sample.")
        if not Path(filename).is_file():
            write(filename, fs, np.zeros(int(seconds * fs), dtype="int16"))

    # ----------------------------------------------
    # Whisper transcription
    # ----------------------------------------------

    model = get_whisper_model()
    result = model.transcribe(
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

    try:
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
    except Exception as exc:
        print(f"Warning: Native microphone unavailable on cloud ({exc}). Using sample audio.")
        if Path("sample.wav").is_file():
            from scipy.io.wavfile import read
            _, recording = read("sample.wav")
            if len(recording.shape) > 1:
                recording = recording[:, 0]
        else:
            recording = np.zeros(int(seconds * fs), dtype="int16")
            write("sample.wav", fs, recording)

    # Convert in-memory int16 audio to normalized float32 for Whisper (no ffmpeg needed)
    audio_float = recording.flatten().astype(np.float32) / 32768.0

    model = get_whisper_model()
    result = model.transcribe(
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
    # Acoustic Environment & Background Analysis
    # ----------------------------------------------

    sound = "Speech / Natural Environment"
    confidence = 0.95
    natural = True

    if Path("sample.wav").is_file():
        try:
            _, wav_data = wav_read("sample.wav")
            if len(wav_data.shape) > 1:
                wav_data = wav_data[:, 0]
            wav_float = wav_data.astype(np.float32) / 32768.0
            rms = float(np.sqrt(np.mean(wav_float**2))) if len(wav_float) > 0 else 0.0

            if rms > 0.45:
                sound = "High Background Noise"
                confidence = 0.85
                natural = False
            elif rms < 0.01:
                sound = "Quiet / Ambient"
                confidence = 0.92
                natural = True
            else:
                sound = "Natural Environment"
                confidence = 0.95
                natural = True
        except Exception:
            pass

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