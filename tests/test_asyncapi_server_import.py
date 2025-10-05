def test_import_server():
    import importlib
    m = importlib.import_module('src.coach_feedback.asyncapi.server')
    assert hasattr(m, 'app')
