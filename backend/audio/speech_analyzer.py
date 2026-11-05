import os
import re
import tempfile
from io import BytesIO

import librosa
import numpy as np
import tensorflow_hub as hub
from scipy.io.wavfile import read as read_wav, write
from backend.services.ai_service_client import transcribe_audio_file


SAMPLE_RATE = 16000
print("Loading YAMNet...")
yamnet = hub.load("https://tfhub.dev/google/yamnet/1")
class_map = yamnet.class_map_path().numpy().decode("utf-8")
with open(class_map, encoding="utf-8") as class_file:
    labels = [line.strip().split(",")[2] for line in class_file.readlines()[1:]]
print("YAMNet loaded.")

def record_and_transcribe(seconds=10, filename="sample.wav"):
    """Transcribe a WAV file already captured by the browser."""
    return transcribe_audio_file(filename).get("transcript", "").strip()


def analyze_speech_audio(audio_data, sample_rate=SAMPLE_RATE):
    """Transcribe browser microphone audio and calculate speech/audio metrics."""
    waveform = np.asarray(audio_data, dtype=np.float32).reshape(-1)
    if sample_rate != SAMPLE_RATE and waveform.size:
        waveform = librosa.resample(waveform, orig_sr=sample_rate, target_sr=SAMPLE_RATE)

    duration = waveform.size / SAMPLE_RATE if waveform.size else 0
    audio_rms = float(np.sqrt(np.mean(np.square(waveform)))) if waveform.size else 0.0
    if duration <= 0.25 or audio_rms < 0.0001:
        return {
            "transcript": "", "fillers": {}, "total_fillers": 0,
            "word_count": 0, "wpm": 0, "background": "Clear",
            "background_confidence": 1.0, "background_natural": True,
            "speech_score": 0, "recorded_seconds": round(duration, 1),
            "speech_seconds": 0, "audio_rms": audio_rms,
        }

    audio_int16 = np.clip(waveform * 32767, -32768, 32767).astype(np.int16)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
        write(temp_path, SAMPLE_RATE, audio_int16)
        transcription = transcribe_audio_file(temp_path)
        transcript = transcription.get("transcript", "").strip()
        speech_duration = float(transcription.get("speech_seconds", 0) or 0)
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
    speech_duration = min(duration, speech_duration) if speech_duration > 0 else duration
    wpm = round(word_count / (speech_duration / 60)) if speech_duration > 0 and word_count else 0

    scores, _, _ = yamnet(waveform)
    mean_scores = np.mean(scores.numpy(), axis=0)
    index = int(np.argmax(mean_scores))
    sound = labels[index]
    confidence = float(mean_scores[index])
    natural = any(
        term.lower() in sound.lower()
        for term in ["Rain", "Thunder", "Wind", "Water", "Ocean", "Bird", "Stream"]
    )

    speech_score = (
        max(0, 100 - total_fillers * 3 - (10 if wpm < 90 or wpm > 170 else 0))
        if transcript else 0
    )
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
        "recorded_seconds": round(duration, 1),
        "speech_seconds": round(speech_duration, 1),
        "audio_rms": audio_rms,
    }


def analyze_speech_wav(wav_bytes):
    """Analyze a WAV recording uploaded directly by the browser microphone widget."""
    sample_rate, audio_data = read_wav(BytesIO(wav_bytes))
    audio_data = np.asarray(audio_data)
    if audio_data.ndim > 1:
        audio_data = np.mean(audio_data.astype(np.float32), axis=1)
    if np.issubdtype(audio_data.dtype, np.integer):
        scale = float(max(abs(np.iinfo(audio_data.dtype).min), np.iinfo(audio_data.dtype).max))
        audio_data = audio_data.astype(np.float32) / scale
    else:
        audio_data = audio_data.astype(np.float32)
    return analyze_speech_audio(audio_data, sample_rate=int(sample_rate))


def analyze_speech(seconds=10, start_event=None, audio_data=None, sample_rate=SAMPLE_RATE):
    """Keep the previous API; cloud calls must supply browser-captured audio_data."""
    if start_event is not None:
        start_event.wait()
    if audio_data is None:
        return analyze_speech_audio(np.array([], dtype=np.float32), sample_rate)
    return analyze_speech_audio(audio_data, sample_rate)
