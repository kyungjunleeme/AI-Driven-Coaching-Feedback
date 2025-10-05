
from __future__ import annotations
import json, tempfile, os, pathlib
import streamlit as st
from typing import List
from .schema import TranscriptChunk, GenerationInput, StepEnum
from .classifier import classify_transcript
from .generator import generate_feedback
from .pipeline.voice_feedback import run_pipeline_on_audio
from .pipeline.voice_feedback_cloud import run_cloud_pipeline

def _load_sample() -> List[TranscriptChunk]:
    sample = [
        {"id":"t1","speaker":"teacher","text":"지난 시간에 질문 뒤 2초를 기다리니 더 많은 학생이 손을 들었어요."},
        {"id":"t2","speaker":"coach","text":"좋아요. 다음에도 일관되게 적용해볼까요?"},
        {"id":"t3","speaker":"teacher","text":"네. 도입 질문마다 체크리스트로 표시해 보겠습니다."}
    ]
    return [TranscriptChunk(**x) for x in sample]

def render_ui():
    st.title("🧑‍🏫 Coach Feedback (Python-only)")
    tabs = st.tabs(["Transcript (text)", "Audio upload", "Cloud mode"])

    # Text tab
    with tabs[0]:
        col1, col2 = st.columns([3,2])
        with col1:
            st.subheader("1) Transcript")
            uploaded = st.file_uploader("Upload transcript JSON (list of {id,speaker,text,ts?})", type=["json"])
            chunks: List[TranscriptChunk] = []
            if uploaded is not None:
                try:
                    data = json.load(uploaded)
                    chunks = [TranscriptChunk(**x) for x in data]
                except Exception as e:
                    st.error(f"Failed to parse JSON: {e}")
            else:
                if st.button("Load sample transcript"):
                    chunks = _load_sample()
            if not chunks:
                st.info("No transcript loaded. Use 'Load sample transcript' for a quick demo.")
            else:
                st.success(f"Loaded {len(chunks)} chunks.")
                st.json([c.model_dump() for c in chunks])

            st.subheader("2) Classify (heuristic demo)")
            if st.button("Run classifier"):
                steps_yaml = pathlib.Path(__file__).with_name("steps.yaml")
                out = classify_transcript(chunks, str(steps_yaml))
                st.json(out.model_dump())

        with col2:
            st.subheader("3) Generate feedback")
            step_id = st.selectbox(
                "Primary step focus",
                options=[(s.value, s.name) for s in StepEnum],
                format_func=lambda x: f"{x[0]:02d} - {x[1].replace('_',' ').title()}"
            )[0]
            lang = st.selectbox("Language", ["ko","en"], index=0)
            if st.button("Generate"):
                if not chunks:
                    chunks = _load_sample()
                gi = GenerationInput(transcript_chunks=chunks, step_focus=StepEnum(step_id), language=lang)
                fb = generate_feedback(gi)
                st.json(fb.model_dump())
                st.markdown("### Preview")
                st.markdown(f"**Praise:** {fb.praise}")
                st.markdown(f"**Improvement:** {fb.improvement}")
                st.markdown(f"**Evidence:** {' '.join(fb.evidence_quote)}")
                st.markdown(f"**Student link:** {fb.student_learning_link}")
                st.markdown(f"**Next step:** {fb.next_step}")

    # Audio tab
    with tabs[1]:
        st.subheader("Upload audio (.wav/.mp3) and generate feedback")
        au = st.file_uploader("Audio file", type=["wav","mp3","m4a","flac","ogg"])
        chosen = st.selectbox("Primary step (optional)", options=["auto"] + [s.value for s in StepEnum])
        if st.button("Run voice pipeline"):
            if au is None:
                st.warning("Please upload an audio file.")
            else:
                fd, tmp = tempfile.mkstemp(suffix="-" + au.name); os.close(fd)
                with open(tmp, "wb") as f: f.write(au.getbuffer())
                with st.spinner("Transcribing & generating feedback..."):
                    step = None if chosen == "auto" else StepEnum(int(chosen))
                    fb = run_pipeline_on_audio(tmp, preferred_step=step)
                st.json(fb.model_dump())
                if st.button("Synthesize TTS of feedback"):
                    from .audio.tts import synthesize_to_wav
                    summary = f"칭찬: {fb.praise}. 개선: {fb.improvement}. 다음 단계: {fb.next_step}."
                    wav = synthesize_to_wav(summary)
                    audio_bytes = open(wav, "rb").read()
                    st.audio(audio_bytes, format="audio/wav")

    # Cloud mode
    with tabs[2]:
        st.header("☁️ Cloud mode (Bedrock + S3 + optional DDB)")
        st.caption("Requires AWS credentials & Bedrock access in your environment")
        au_cloud = st.file_uploader("Audio for cloud pipeline (.wav/.mp3)", type=["wav","mp3","m4a","flac","ogg"], key="au_cloud")
        force_step = st.selectbox("Force step (optional)", options=[None] + [s.value for s in StepEnum])
        lang_cloud = st.selectbox("Language", ["ko","en"], index=0, key="lang_cloud")
        if st.button("Run Cloud pipeline (ASR → Bedrock → S3/DDB)"):
            if au_cloud is None:
                st.warning("Upload an audio file first.")
            else:
                fd, tmp = tempfile.mkstemp(suffix="-" + au_cloud.name); os.close(fd)
                with open(tmp, "wb") as f: f.write(au_cloud.getbuffer())
                with st.spinner("Running cloud pipeline..."):
                    try:
                        result = run_cloud_pipeline(tmp, force_step=force_step, language=lang_cloud)
                        st.success("Done")
                        st.json(result)
                    except Exception as e:
                        st.error(f"Cloud pipeline error: {e}")


    # ---- AsyncAPI Docs ----
    with st.expander("📄 AsyncAPI Docs Viewer (static)"):
        try:
            import yaml, io, html
            from pathlib import Path
            spec_path = Path(__file__).with_name("asyncapi") / "asyncapi.yaml"
            raw = spec_path.read_text(encoding="utf-8")
            st.code(raw, language="yaml")
            # Build a minimal static HTML for download
            html_doc = f"""<!DOCTYPE html>
<html lang="en"><meta charset="utf-8"><title>AsyncAPI (static)</title>
<style>body{{font-family:ui-monospace,Menlo,Consolas,monospace;line-height:1.35;padding:24px;background:#0f172a;color:#e5e7eb}} pre{{white-space:pre-wrap;word-wrap:break-word;background:#111827;padding:16px;border-radius:12px}}</style>
<h1>AsyncAPI spec</h1><pre>{html.escape(raw)}</pre></html>"""
            from pathlib import Path as _P
            out = _P("asyncapi_static.html")
            out.write_text(html_doc, encoding="utf-8")
            st.download_button("Download static HTML", data=html_doc, file_name="asyncapi.html", mime="text/html")
        except Exception as e:
            st.warning(f"AsyncAPI doc render error: {e}")
