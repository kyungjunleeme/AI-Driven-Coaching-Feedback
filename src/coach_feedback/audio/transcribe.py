
from __future__ import annotations
from typing import List, Tuple
from faster_whisper import WhisperModel

def transcribe_audio(audio_path: str, model_size: str = "small", device: str = "cpu", compute_type: str = "int8") -> Tuple[str, List[dict]]:
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    segments_gen, info = model.transcribe(audio_path, vad_filter=True)
    segs, texts = [], []
    for seg in segments_gen:
        segs.append({"start": float(seg.start), "end": float(seg.end), "text": seg.text.strip()})
        texts.append(seg.text.strip())
    full_text = " ".join(texts).strip()
    return full_text, segs
