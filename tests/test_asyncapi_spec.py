from pathlib import Path
def test_spec_exists():
    p = Path('src/coach_feedback/asyncapi/asyncapi.yaml')
    assert p.exists()
