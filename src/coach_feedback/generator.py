from __future__ import annotations
from typing import List
from .schema import TranscriptChunk, GenerationInput, FeedbackOutput, StepEnum


def _pick_quotes(chunks: List[TranscriptChunk], max_q: int = 2) -> List[str]:
    qs = []
    for ch in chunks:
        t = ch.text.strip()
        if t and len(qs) < max_q:
            if len(t) > 160:
                t = t[:157] + "..."
            qs.append(f'"{t}"')
    return qs or ['"(no direct quote available)"']


def generate_feedback(gi: GenerationInput) -> FeedbackOutput:
    step = gi.step_focus
    quotes = _pick_quotes(gi.transcript_chunks, 2)
    if step == StepEnum.LINK_PRAISE_TO_STUDENT_LEARNING:
        praise = "질문 후 잠시 기다린 점이 좋았습니다—그 덕분에 더 많은 학생이 손을 들고 근거를 설명했습니다."
        improvement = "다음 시간에도 질문 뒤 2초 멈춤을 일관되게 적용하고, 이름 부르기 전 전체에게 생각 시간을 주세요."
        student_link = "잠깐의 대기 시간이 참여와 정교화를 높여 학습 품질을 끌어올립니다."
        why = "대기 시간(wait time)은 인지부하를 낮추고 더 많은 학생이 말할 기회를 확보하게 해 참여·정교화를 촉진합니다."
        next_step = "도입·정리 단계의 핵심 질문마다 2초 멈춤 체크박스를 수업 스크립트에 추가하세요."
    else:
        praise = "구체적 실행 계획을 짧고 명확하게 정리한 점이 좋았습니다."
        improvement = (
            "계획에 관찰 지표 1개(예: 손들기 수, 근거 발화 수)를 추가해 다음 수업에서 비교하세요."
        )
        student_link = "구체적 계획은 학생 활동 흐름을 매끈하게 만들어 참여를 높입니다."
        why = "명시적 계획은 교사의 주의 전환 비용을 낮추고 학생 행동 지표의 변화를 추적 가능하게 합니다."
        next_step = "다음 수업 개시 5분 내 체크리스트(질문·자료·자리배치)를 미리 점검하세요."
    return FeedbackOutput(
        step_focus=step,
        praise=praise,
        improvement=improvement,
        why_it_matters=why,
        evidence_quote=quotes,
        student_learning_link=student_link,
        next_step=next_step,
        confidence=0.75,
    )
