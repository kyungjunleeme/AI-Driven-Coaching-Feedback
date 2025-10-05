from __future__ import annotations
import pyttsx3
import tempfile
import os


def synthesize_to_wav(text: str, out_path: str | None = None) -> str:
    engine = pyttsx3.init()
    rate = engine.getProperty("rate")
    engine.setProperty("rate", int(rate * 0.9))
    if out_path is None:
        fd, tmp = tempfile.mkstemp(suffix=".wav", prefix="tts_")
        os.close(fd)
        out_path = tmp
    engine.save_to_file(text, out_path)
    engine.runAndWait()
    return out_path
