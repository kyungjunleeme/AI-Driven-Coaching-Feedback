def test_cognito_dependency_factory_import():
    from src.coach_feedback.auth.cognito import cognito_auth_dependency

    assert callable(cognito_auth_dependency)
