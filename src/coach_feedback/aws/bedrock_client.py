from __future__ import annotations
from typing import List, Dict, Any, Optional
import json
import boto3
from botocore.config import Config
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from .config import AWS_REGION, AWS_PROFILE, BEDROCK_MODEL_ID
from jinja2 import Template
from ..templates_loader import load_template
from ..llm.parallel import parallel_scores_per_step
from ..llm.rate import SimpleRateLimiter

STEP_NAMES = {
    1: "Review prior progress",
    2: "Form hypothesis / observation insight",
    3: "Select action step",
    4: "Agree & clarify step",
    5: "Model / Demonstrate step",
    6: "Explain rationale / insight",
    7: "Plan implementation",
    8: "Rehearse / practice",
    9: "Feedback & adjust",
    10: "Implementation / observation",
    11: "Link praise to student learning",
    12: "Next step & habit building",
}


def _session():
    if AWS_PROFILE:
        return boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    return boto3.Session(region_name=AWS_REGION)


def _bedrock_runtime():
    return _session().client("bedrock-runtime", region_name=AWS_REGION)


def render_with_jinja2(tpl_name: str, **ctx) -> str:
    tpl = load_template(tpl_name)
    return Template(tpl).render(**ctx)


def build_step_classifier_prompt(chunk_text: str, step_id: int) -> str:
    return render_with_jinja2(
        "step_classifier.j2", step_name=STEP_NAMES[step_id], step_id=step_id, chunk_text=chunk_text
    )


def build_feedback_prompt(
    transcript: List[Dict[str, Any]], step_focus: int, language: str = "ko"
) -> str:
    return render_with_jinja2(
        "feedback_generator.j2",
        transcript_json=json.dumps(transcript, ensure_ascii=False),
        step_focus=step_focus,
        language=language,
    )


def _invoke_claude(
    prompt: str, system: Optional[str] = None, max_tokens: int = 400, temperature: float = 0.2
) -> str:
    runtime = _bedrock_runtime()
    model_id = BEDROCK_MODEL_ID
    messages = []
    if system:
        messages.append({"role": "system", "content": [{"type": "text", "text": system}]})
    messages.append({"role": "user", "content": [{"type": "text", "text": prompt}]})
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
    }
    resp = runtime.invoke_model(
        modelId=model_id,
        body=json.dumps(body).encode("utf-8"),
        accept="application/json",
        contentType="application/json",
    )
    payload = json.loads(resp["body"].read().decode("utf-8"))
    parts = payload.get("content", [])
    text = ""
    for p in parts:
        if p.get("type") == "text":
            text += p.get("text", "")
    return text


def classify_chunk_parallel_scores_concurrent(
    chunk_text: str, step_ids: List[int] = list(range(1, 13))
) -> Dict[int, float]:
    def scorer(step_id: int) -> float:
        prompt = build_step_classifier_prompt(chunk_text, step_id)
        out = _invoke_claude(
            prompt, system="Classify coaching step", max_tokens=200, temperature=0.0
        )
        try:
            data = json.loads(out)
            return float(data.get("score", 0.0))
        except Exception:
            return 0.0

    return parallel_scores_per_step(step_ids, scorer=scorer, max_workers=min(12, len(step_ids)))


def generate_feedback_cloud(
    transcript: List[Dict[str, Any]], step_focus: int, language: str = "ko"
) -> Dict[str, Any]:
    prompt = build_feedback_prompt(transcript, step_focus, language=language)
    out = _invoke_claude(
        prompt, system="Generate instructional coaching feedback", max_tokens=600, temperature=0.2
    )
    try:
        data = json.loads(out)
    except Exception:
        data = {
            "praise": "수업에서 잘한 점을 구체적으로 칭찬합니다.",
            "improvement": "다음 수업에서 시도할 1가지 개선 행동을 제안합니다.",
            "why_it_matters": "교육적 근거를 간단히 설명합니다.",
            "evidence_quote": ["(인용 불가)"],
            "student_learning_link": "칭찬을 학생 학습과 명시적으로 연결합니다.",
            "next_step": "다음 액션 스텝을 한 가지 지시합니다.",
        }
    return data




def _bedrock_runtime_cfg(timeout_s: int = 20, max_attempts: int = 0):
    cfg = Config(read_timeout=timeout_s, retries={"max_attempts": max_attempts})
    return _session().client("bedrock-runtime", region_name=AWS_REGION, config=cfg)


def _invoke_claude_cfg(
    prompt: str, system: Optional[str], max_tokens: int, temperature: float, timeout_s: int
):
    rt = _bedrock_runtime_cfg(timeout_s=timeout_s, max_attempts=0)
    model_id = BEDROCK_MODEL_ID
    messages = []
    if system:
        messages.append({"role": "system", "content": [{"type": "text", "text": system}]})
    messages.append({"role": "user", "content": [{"type": "text", "text": prompt}]})
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
    }
    resp = rt.invoke_model(
        modelId=model_id,
        body=json.dumps(body).encode("utf-8"),
        accept="application/json",
        contentType="application/json",
    )
    payload = json.loads(resp["body"].read().decode("utf-8"))
    parts = payload.get("content", [])
    text = ""
    for p in parts:
        if p.get("type") == "text":
            text += p.get("text", "")
    return text


def _retry(fn, retries: int = 2, base: float = 0.6, cap: float = 2.5):
    last_err = None
    for i in range(retries + 1):
        try:
            return fn()
        except Exception as e:
            last_err = e
            if i == retries:
                raise
            delay = min(cap, base * (2**i)) + random.random() * 0.2
            time.sleep(delay)
    if last_err:
        raise last_err


def score_chunks_steps(
    texts: list[str],
    step_ids: list[int] = list(range(1, 13)),
    max_workers: int = 24,
    timeout_s: int = 20,
    retries: int = 2,
    calls_per_sec: float = 8.0,
    initial_stagger_ms: int = 50,
) -> list[dict[int, float]]:
    """Return per-chunk dict of step->score using multi-chunk×multi-step parallel calls with retry and rate limit."""
    limiter = SimpleRateLimiter(calls_per_sec)
    results: list[dict[int, float]] = [dict() for _ in texts]

    def task(ci: int, sid: int):
        prompt = build_step_classifier_prompt(texts[ci], sid)

        def call():
            limiter.acquire()
            out = _invoke_claude_cfg(
                prompt,
                system="Classify coaching step",
                max_tokens=200,
                temperature=0.0,
                timeout_s=timeout_s,
            )
            try:
                data = json.loads(out)
                return float(data.get("score", 0.0))
            except Exception:
                return 0.0

        sc = _retry(call, retries=retries)
        results[ci][sid] = sc

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        # initial staggering to avoid burst
        futs = []
        for ci, _ in enumerate(texts):
            for sid in step_ids:
                futs.append(ex.submit(task, ci, sid))
                time.sleep(initial_stagger_ms / 1000.0)
        for f in as_completed(futs):
            _ = f.result()
    return results


def top_step_per_chunk(texts: list[str]) -> list[int]:
    scores = score_chunks_steps(texts)
    tops = []
    for d in scores:
        if not d:
            tops.append(11)
        else:
            tops.append(max(d, key=lambda k: d[k]))
    return tops
