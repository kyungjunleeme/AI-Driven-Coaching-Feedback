def test_server_handler_import():
    import importlib

    m = importlib.import_module("src.coach_feedback.asyncapi.server")
    assert hasattr(m, "app")
