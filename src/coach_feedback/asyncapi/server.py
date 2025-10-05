from __future__ import annotations
import json
import asyncio
from typing import Dict, Set, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Body
from fastapi.responses import JSONResponse
from jsonschema import validate, ValidationError
from ..schema import StepEnum, TranscriptChunk
from ..generator import generate_feedback
from ..pipeline.voice_feedback import run_pipeline_on_audio
from ..pipeline.voice_feedback_cloud import run_cloud_pipeline
from .schemas import RequestFeedbackSchema

app = FastAPI(title="Coach Feedback Event Server")

# session_id -> set of websockets
SUBS: Dict[str, Set[WebSocket]] = {}


async def _broadcast(session_id: str, message: dict):
    dead = set()
    for ws in SUBS.get(session_id, set()):
        try:
            await ws.send_text(json.dumps(message, ensure_ascii=False))
        except Exception:
            dead.add(ws)
    if dead:
        SUBS[session_id] -= dead


@app.websocket("/ws/sessions/{session_id}")
async def ws_session(websocket: WebSocket, session_id: str):
    await websocket.accept()
    SUBS.setdefault(session_id, set()).add(websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            # Optionally handle incoming commands over WS
            try:
                msg = json.loads(raw)
            except Exception:
                await websocket.send_text(json.dumps({"type": "Error", "error": "Invalid JSON"}))
                continue
            # Handle command
            if isinstance(msg, dict) and msg.get("type") == "RequestFeedback":
                await handle_request_feedback(session_id, msg)
            else:
                await websocket.send_text(
                    json.dumps({"type": "Ack", "receivedType": msg.get("type")})
                )
    except WebSocketDisconnect:
        SUBS.get(session_id, set()).discard(websocket)


@app.post("/publish/{session_id}")
async def publish(session_id: str, message: Dict[str, Any] = Body(...)):
    # HTTP entrypoint so Python pipelines can publish without persistent WS
    await _broadcast(session_id, message)
    return JSONResponse({"ok": True})


# Convenience endpoints
@app.get("/healthz")
async def healthz():
    return {"ok": True, "sessions": {k: len(v) for k, v in SUBS.items()}}


async def handle_request_feedback(session_id: str, msg: dict):
    # Validate payload
    try:
        validate(instance=msg, schema=RequestFeedbackSchema)
    except ValidationError as e:
        await _broadcast(session_id, {"type": "Error", "error": f"ValidationError: {e.message}"})
        return

    mode = msg.get("mode", "local")
    force_step = msg.get("force_step")
    language = msg.get("language", "ko")
    audio_ref = msg.get("audio_ref")

    async def run():
        try:
            if mode == "cloud":
                if not audio_ref:
                    # cloud without audio: return error
                    return {"error": "audio_ref required for cloud mode"}
                # If audio_ref is s3://..., we assume pipeline can fetch via boto3 in future; here expect local path or s3 handled in pipeline
                result = run_cloud_pipeline(audio_ref, force_step=force_step, language=language)
                payload = result
            else:
                # local mode: if no audio, create minimal feedback from sample transcript
                if audio_ref:
                    fb = run_pipeline_on_audio(
                        audio_ref, preferred_step=StepEnum(force_step) if force_step else None
                    )
                    payload = {
                        "session_id": session_id,
                        "step_focus": int(fb.step_focus),
                        "feedback": fb.model_dump(),
                    }
                else:
                    # fallback: synthesize from sample transcript through generator
                    chunks = [
                        TranscriptChunk(
                            id="t1",
                            speaker="teacher",
                            text="지난 시간에 질문 뒤 2초를 기다리니 더 많은 학생이 손을 들었어요.",
                        )
                    ]
                    from ..schema import GenerationInput

                    gi = GenerationInput(
                        transcript_chunks=chunks,
                        step_focus=StepEnum.LINK_PRAISE_TO_STUDENT_LEARNING,
                        language=language,
                    )
                    fb = generate_feedback(gi)
                    payload = {
                        "session_id": session_id,
                        "step_focus": int(fb.step_focus),
                        "feedback": fb.model_dump(),
                    }
            return payload
        except Exception as e:
            return {"error": str(e)}

    # run in thread to avoid blocking WS loop
    payload = await asyncio.to_thread(lambda: asyncio.run(run()))
    if isinstance(payload, dict) and payload.get("error"):
        await _broadcast(session_id, {"type": "Error", "error": payload.get("error")})
        return

    # Emit FeedbackCreated
    await _broadcast(session_id, {"type": "FeedbackCreated", **payload})


@app.post("/commands/request-feedback/{session_id}")
async def http_request_feedback(session_id: str, message: dict = Body(...)):
    message.setdefault("type", "RequestFeedback")
    await handle_request_feedback(session_id, message)
    return JSONResponse({"ok": True})
