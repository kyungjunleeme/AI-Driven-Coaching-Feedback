from src.coach_feedback.aws import bedrock_client as bc


def test_top_step_per_chunk_monkey(monkeypatch):
    def fake_invoke_cfg(prompt: str, system=None, max_tokens=0, temperature=0, timeout_s=0):
        # assign higher score when step id is 3 for text containing "plan", else 11
        import re
        import json as _json

        m = re.search(r"ID\s(\d+)", prompt)
        sid = int(m.group(1)) if m else 0
        score = 0.9 if sid in (3, 11) else 0.1
        return _json.dumps({"score": score})

    monkeypatch.setattr(bc, "_invoke_claude_cfg", fake_invoke_cfg)
    tops = bc.top_step_per_chunk(["let's plan", "students improved"])
    assert len(tops) == 2
