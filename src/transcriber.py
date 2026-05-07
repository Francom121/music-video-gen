"""Transcribe audio via Whisper (local) or OpenAI API. Returns word-level timestamps."""
import os


def transcribe(path, method="local", model="medium"):
    """Returns list of {word, start, end} dicts with word-level timestamps."""
    if method == "local":
        return _transcribe_local(path, model)
    if method == "api":
        return _transcribe_api(path)
    raise ValueError(f"Unknown transcription method: {method}")


def _transcribe_local(path, model_size):
    """Run openai-whisper locally. Slow on CPU but no API cost."""
    import whisper
    print(f"      Loading whisper model '{model_size}' (first run downloads weights)...")
    model = whisper.load_model(model_size)
    print(f"      Transcribing... (this can take several minutes)")
    result = model.transcribe(path, word_timestamps=True)

    words = []
    for segment in result.get("segments", []):
        for w in segment.get("words", []):
            words.append({
                "word": w.get("word", "").strip(),
                "start": float(w.get("start", 0.0)),
                "end": float(w.get("end", 0.0)),
            })
    return words


def _transcribe_api(path):
    """Use OpenAI's Whisper API. Faster, costs ~$0.006/minute."""
    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    with open(path, "rb") as f:
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",
            timestamp_granularities=["word"],
        )
    words = []
    for w in getattr(result, "words", []) or []:
        words.append({
            "word": w.word.strip() if hasattr(w, "word") else w["word"].strip(),
            "start": float(w.start if hasattr(w, "start") else w["start"]),
            "end": float(w.end if hasattr(w, "end") else w["end"]),
        })
    return words
