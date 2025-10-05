from __future__ import annotations
from typing import List, Optional
from ..schema import TranscriptChunk, GenerationInput, StepEnum, FeedbackOutput
from ..classifier import classify_transcript
from ..generator import generate_feedback
from ..audio.transcribe import transcribe_audio
import pathlib


def audio_to_transcript_chunks(audio_path: str) -> List[TranscriptChunk]:
    full_text, segments = transcribe_audio(audio_path)
    chunks = [
        TranscriptChunk(id=f"seg{i}", speaker="teacher", text=s["text"])
        for i, s in enumerate(segments, start=1)
    ]
    if not chunks and full_text:
        chunks = [TranscriptChunk(id="t1", speaker="teacher", text=full_text)]
    return chunks


def run_pipeline_on_audio(
    audio_path: str, preferred_step: Optional[StepEnum] = None
) -> FeedbackOutput:
    chunks = audio_to_transcript_chunks(audio_path)
    steps_yaml = pathlib.Path(__file__).parents[1] / "steps.yaml"
    cl_out = classify_transcript(chunks, str(steps_yaml))
    top_step = preferred_step
    if top_step is None:
        max_conf = -1.0
        for lab in cl_out.labels:
            if lab.step_ids and lab.confidence > max_conf:
                top_step = lab.step_ids[0]
                max_conf = lab.confidence
        if top_step is None:
            top_step = StepEnum.LINK_PRAISE_TO_STUDENT_LEARNING
    gi = GenerationInput(transcript_chunks=chunks, step_focus=top_step)
    fb = generate_feedback(gi)
    try:
        session_id = "local-" + chunks[0].id
        payload = {
            "session_id": session_id,
            "step_focus": int(fb.step_focus),
            "feedback": fb.model_dump(),
        }
        _maybe_publish_asyncapi(session_id, payload)
    except Exception:
        pass
    return fb


# --- AsyncAPI publish hook (optional) ---
def _maybe_publish_asyncapi(session_id: str, data: dict):
    import os

    if os.getenv("ASYNCAPI_ENABLE", "0") != "1":
        return
    try:
        from ..asyncapi.publisher import publish_event

        publish_event(session_id, "FeedbackCreated", data)
    except Exception:
        pass
