from backend.services.ai_service_client import transcribe_file as _transcribe_remote


def transcribe_file(audio_file="sample.wav"):
    return _transcribe_remote(audio_file)


if __name__ == "__main__":
    print(transcribe_file())
