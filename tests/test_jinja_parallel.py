from src.coach_feedback.aws import bedrock_client as bc


def test_render_jinja_templates():
    txt = bc.render_with_jinja2(
        "step_classifier.j2", step_name="Test Step", step_id=99, chunk_text="hello"
    )
    assert "Test Step" in txt and "hello" in txt


def test_parallel_scores_monkeypatch(monkeypatch):
    def fake_invoke(prompt: str, system=None, max_tokens=0, temperature=0):
        import re
        import json as _json

        m = re.search(r"ID\s(\d+)", prompt)
        sid = int(m.group(1)) if m else 0
        return _json.dumps({"score": 0.1 * (sid % 10)})

    monkeypatch.setattr(bc, "_invoke_claude", fake_invoke)
    scores = bc.classify_chunk_parallel_scores_concurrent("text", list(range(1, 6)))
    assert len(scores) == 5 and max(scores.values()) > 0.0
