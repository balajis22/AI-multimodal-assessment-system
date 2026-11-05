import os
import re
import tempfile

import librosa
import numpy as np
import tensorflow_hub as hub
from faster_whisper import WhisperModel
from scipy.io.wavfile import write


SAMPLE_RATE = 16000
print("Loading YAMNet...")
yamnet = hub.load("https://tfhub.dev/google/yamnet/1")
class_map = yamnet.class_map_path().numpy().decode("utf-8")
with open(class_map, encoding="utf-8") as class_file:
    labels = [line.strip().split(",")[2] for line in class_file.readlines()[1:]]
print("YAMNet loaded.")

whisper_model = None


def _transcribe_file(filename):
    global whisper_model
    if whisper_model is None:
        print("Loading CPU Whisper model...")
        whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = whisper_model.transcribe(filename, beam_size=5)
    return " ".join(segment.text.strip() for segment in segments).strip()


def record_and_transcribe(seconds=10, filename="sample.wav"):
    """Transcribe a WAV file already captured by the browser."""
    return _transcribe_file(filename)


def analyze_speech_audio(audio_data, sample_rate=SAMPLE_RATE):
    """Transcribe browser microphone audio and calculate speech/audio metrics."""
    waveform = np.asarray(audio_data, dtype=np.float32).reshape(-1)
    if sample_rate != SAMPLE_RATE and waveform.size:
        waveform = librosa.resample(waveform, orig_sr=sample_rate, target_sr=SAMPLE_RATE)

    duration = waveform.size / SAMPLE_RATE if waveform.size else 0
    if duration <= 0.25:
        return {
            "transcript": "", "fillers": {}, "total_fillers": 0,
            "word_count": 0, "wpm": 0, "background": "Clear",
            "background_confidence": 1.0, "background_natural": True,
            "speech_score": 75,
        }

    audio_int16 = np.clip(waveform * 32767, -32768, 32767).astype(np.int16)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
        write(temp_path, SAMPLE_RATE, audio_int16)
        transcript = _transcribe_file(temp_path)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

    text = transcript.lower()
    fillers = ["um", "uh", "like", "actually", "basically", "you know", "sort of", "kind of", "so"]
    filler_counts = {
        filler: len(re.findall(r"\b" + re.escape(filler) + r"\b", text))
        for filler in fillers
    }
    total_fillers = sum(filler_counts.values())
    word_count = len(text.split())
    wpm = round(word_count / (duration / 60))

    scores, _, _ = yamnet(waveform)
    mean_scores = np.mean(scores.numpy(), axis=0)
    index = int(np.argmax(mean_scores))
    sound = labels[index]
    confidence = float(mean_scores[index])
    natural = any(
        term.lower() in sound.lower()
        for term in ["Rain", "Thunder", "Wind", "Water", "Ocean", "Bird", "Stream"]
    )

    speech_score = max(0, 100 - total_fillers * 3 - (10 if wpm < 90 or wpm > 170 else 0))
    return {
        "transcript": transcript,
        "fillers": filler_counts,
        "total_fillers": total_fillers,
        "word_count": word_count,
        "wpm": wpm,
        "background": sound,
        "background_confidence": confidence,
        "background_natural": natural,
        "speech_score": speech_score,
    }


def analyze_speech(seconds=10, start_event=None, audio_data=None, sample_rate=SAMPLE_RATE):
    """Keep the previous API; cloud calls must supply browser-captured audio_data."""
    if start_event is not None:
        start_event.wait()
    if audio_data is None:
        return analyze_speech_audio(np.array([], dtype=np.float32), sample_rate)
    return analyze_speech_audio(audio_data, sample_rate)
