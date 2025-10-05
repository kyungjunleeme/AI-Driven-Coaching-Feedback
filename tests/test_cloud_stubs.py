import pytest
from src.coach_feedback.aws import bedrock_client as bc


@pytest.mark.cloud
def test_cloud_imports():
    assert callable(bc.classify_chunk_parallel_scores_concurrent)
    assert callable(bc.generate_feedback_cloud)
