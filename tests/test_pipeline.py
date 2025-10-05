from src.coach_feedback.schema import TranscriptChunk, GenerationInput, StepEnum
from src.coach_feedback.classifier import classify_transcript
from src.coach_feedback.generator import generate_feedback
import pathlib


def test_classifier_and_generator_roundtrip():
    chunks = [
        TranscriptChunk(id="t1", speaker="teacher", text="지난 시간 이후, 학생들이 더 참여했어요."),
        TranscriptChunk(
            id="t2", speaker="coach", text="좋아요. 다음엔 질문 뒤 2초 멈춤을 시도해봐요."
        ),
    ]
    steps_yaml = pathlib.Path(__file__).parents[1] / "src" / "coach_feedback" / "steps.yaml"
    out = classify_transcript(chunks, str(steps_yaml))
    assert len(out.labels) == 2
    gi = GenerationInput(
        transcript_chunks=chunks, step_focus=StepEnum.LINK_PRAISE_TO_STUDENT_LEARNING
    )
    fb = generate_feedback(gi)
    assert fb.praise and fb.improvement and fb.student_learning_link
    assert len(fb.evidence_quote) >= 1
