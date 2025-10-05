
from src.coach_feedback.schema import TranscriptChunk, GenerationInput, StepEnum, FeedbackOutput

def test_models_basic():
    ch = TranscriptChunk(id="a", speaker="teacher", text="hello")
    gi = GenerationInput(transcript_chunks=[ch], step_focus=StepEnum.LINK_PRAISE_TO_STUDENT_LEARNING)
    assert gi.step_focus == StepEnum.LINK_PRAISE_TO_STUDENT_LEARNING
    fb = FeedbackOutput(
        step_focus=StepEnum.LINK_PRAISE_TO_STUDENT_LEARNING,
        praise="좋습니다.",
        improvement="다음엔 2초 대기 시간을 넣어보세요.",
        why_it_matters="대기 시간은 참여를 높입니다.",
        evidence_quote=[""hello""],
        student_learning_link="참여를 높여 학습 품질이 향상됩니다.",
        next_step="도입 질문마다 2초 멈춤을 적용하세요.",
        confidence=0.8,
    )
    assert fb.confidence == 0.8
