import whisper
from collections import Counter

print("Loading Whisper model...")

model = whisper.load_model("base")

print("Model loaded!")

audio_file = "sample.wav"

result = model.transcribe(audio_file)

transcript = result["text"]

print("\nTranscript:")
print(transcript)

# -----------------------------
# Filler Word Detection
# -----------------------------

fillers = [
    "um",
    "uh",
    "like",
    "actually",
    "basically",
    "you know",
    "so"
]

words = transcript.lower().split()

counter = Counter(words)

print("\n--------------------------")
print("FILLER WORDS")
print("--------------------------")

total = 0

for filler in fillers:

    count = counter[filler]

    if count > 0:
        print(f"{filler:<12}: {count}")

    total += count

print("--------------------------")
print("Total fillers:", total)