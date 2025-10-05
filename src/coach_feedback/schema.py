
from __future__ import annotations
from enum import IntEnum
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, constr, conlist, confloat

class StepEnum(IntEnum):
    REVIEW_PRIOR_PROGRESS = 1
    FORM_HYPOTHESIS = 2
    SELECT_ACTION_STEP = 3
    AGREE_CLARIFY = 4
    MODEL_DEMONSTRATE = 5
    EXPLAIN_RATIONALE = 6
    PLAN_IMPLEMENTATION = 7
    REHEARSE_PRACTICE = 8
    FEEDBACK_ADJUST = 9
    IMPLEMENT_OBSERVE = 10
    LINK_PRAISE_TO_STUDENT_LEARNING = 11
    NEXT_STEP_HABIT = 12

class TranscriptChunk(BaseModel):
    id: str = Field(..., description="Unique chunk ID")
    speaker: Literal["coach", "teacher", "other"]
    text: str = Field(..., min_length=1)
    ts: Optional[str] = Field(None, description="ISO8601 timestamp")

class ClassroomObservation(BaseModel):
    notes: Optional[str] = None

class TaskArtifact(BaseModel):
    name: str
    description: Optional[str] = None

class MetaData(BaseModel):
    subject: Optional[str] = None
    grade: Optional[str] = None
    session_type: Optional[str] = None
    locale: Optional[Literal["ko", "en"]] = "ko"

class GenerationInput(BaseModel):
    transcript_chunks: conlist(TranscriptChunk, min_items=1)
    observation: Optional[ClassroomObservation] = None
    artifacts: Optional[List[TaskArtifact]] = None
    metadata: Optional[MetaData] = None
    step_focus: StepEnum
    secondary_steps: Optional[List[StepEnum]] = None
    language: Optional[Literal["ko", "en"]] = "ko"

class StepLabel(BaseModel):
    id: str
    step_ids: List[StepEnum] = Field(default_factory=list)
    confidence: confloat(ge=0.0, le=1.0) = 0.0

class ClassificationOutput(BaseModel):
    labels: List[StepLabel]
    notes: Optional[constr(max_length=300)] = None

class FeedbackOutput(BaseModel):
    step_focus: StepEnum
    praise: constr(strip_whitespace=True, min_length=1, max_length=600)
    improvement: constr(strip_whitespace=True, min_length=1, max_length=700)
    why_it_matters: constr(strip_whitespace=True, min_length=1, max_length=900)
    evidence_quote: conlist(constr(min_length=1), min_items=1, max_items=2)
    student_learning_link: constr(strip_whitespace=True, min_length=1, max_length=400)
    next_step: constr(strip_whitespace=True, min_length=1, max_length=600)
    confidence: confloat(ge=0.0, le=1.0)
