from __future__ import annotations
from typing import List, Optional, Dict, Any
from ..schema import TranscriptChunk
from ..audio.transcribe import transcribe_audio
from ..aws.bedrock_client import classify_chunk_parallel_scores_concurrent, generate_feedback_cloud
from ..aws.s3_io import upload_file, upload_json
from ..aws.ddb_io import put_feedback
import uuid


def audio_to_chunks(audio_path: str) -> List[TranscriptChunk]:
    full_text, segments = transcribe_audio(audio_path)
    chunks = [
        TranscriptChunk(id=f"seg{i}", speaker="teacher", text=s["text"])
        for i, s in enumerate(segments, start=1)
    ]
    if not chunks and full_text:
        chunks = [TranscriptChunk(id="t1", speaker="teacher", text=full_text)]
    return chunks


def detect_primary_step(chunks: List[TranscriptChunk]) -> int:
    votes = {}
    for ch in chunks:
        scores = classify_chunk_parallel_scores_concurrent(ch.text)
        sid = max(scores, key=lambda k: scores[k]) if scores else 11
        votes[sid] = votes.get(sid, 0.0) + 1.0
    return max(votes, key=lambda k: votes[k]) if votes else 11


def run_cloud_pipeline(
    audio_path: str, force_step: Optional[int] = None, language: str = "ko"
) -> Dict[str, Any]:
    chunks = audio_to_chunks(audio_path)
    transcript = [c.model_dump() for c in chunks]
    step_focus = force_step or detect_primary_step(chunks)
    fb = generate_feedback_cloud(transcript, step_focus, language=language)

    session_id = str(uuid.uuid4())[:8]
    key_audio = f"sessions/{session_id}/input/audio.wav"
    key_json = f"sessions/{session_id}/output/feedback.json"
    try:
        s3_audio = upload_file(audio_path, key_audio)
    except Exception:
        s3_audio = None
    out_obj = {
        "session_id": session_id,
        "step_focus": step_focus,
        "transcript": transcript,
        "feedback": fb,
        "audio_s3": s3_audio,
    }
    try:
        s3_json = upload_json(out_obj, key_json)
        out_obj["feedback_s3"] = s3_json
    except Exception:
        pass
    try:
        put_feedback(session_id, out_obj)
    except Exception:
        pass
    _maybe_publish_asyncapi(session_id, out_obj)
    return out_obj


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
