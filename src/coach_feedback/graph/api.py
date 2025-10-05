from __future__ import annotations
import json
import os
import strawberry
from typing import List, Optional
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from fastapi import Depends
from ..auth.cognito import cognito_auth_dependency, AUTH_REQUIRED


@strawberry.type
class TranscriptChunkType:
    id: str
    speaker: str
    text: str
    ts: Optional[str] = None


@strawberry.type
class FeedbackType:
    step_focus: int
    praise: str
    improvement: str
    why_it_matters: str
    evidence_quote: List[str]
    student_learning_link: str
    next_step: str


@strawberry.type
class SessionType:
    session_id: str
    step_focus: int
    transcript: List[TranscriptChunkType]
    feedback: FeedbackType
    audio_s3: Optional[str] = None
    feedback_s3: Optional[str] = None


SESSIONS_DIR = os.getenv("SESSIONS_DIR", "data/sessions")


def _load_session(session_id: str) -> Optional[dict]:
    path = os.path.join(SESSIONS_DIR, session_id, "output", "feedback.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@strawberry.type
class Query:
    @strawberry.field
    def get_session(self, session_id: str) -> Optional[SessionType]:
        data = _load_session(session_id)
        if not data:
            return None
        fb = data["feedback"]
        return SessionType(
            session_id=data["session_id"],
            step_focus=data["step_focus"],
            transcript=[TranscriptChunkType(**t) for t in data["transcript"]],
            feedback=FeedbackType(**fb),
            audio_s3=data.get("audio_s3"),
            feedback_s3=data.get("feedback_s3"),
        )


schema = strawberry.Schema(query=Query)
app = FastAPI()
deps = [Depends(cognito_auth_dependency())] if AUTH_REQUIRED else None
graphql_app = GraphQLRouter(schema, dependencies=deps)
app.include_router(graphql_app, path="/graphql")
