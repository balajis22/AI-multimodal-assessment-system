from faster_whisper import WhisperModel


def transcribe_file(audio_file="sample.wav"):
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio_file, beam_size=5)
    return " ".join(segment.text.strip() for segment in segments).strip()


if __name__ == "__main__":
    print(transcribe_file())
