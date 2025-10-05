def test_appsync_signer_import():
    from src.coach_feedback.aws.appsync_iam import post_graphql_iam
    assert callable(post_graphql_iam)
