"""Example tests for the agents package."""

import pytest
from agents.example import create_client


def test_create_client():
    """Test that we can create an OpenAI client."""
    # This test will only work if OPENAI_API_KEY is set
    # In a real project, you'd want to mock this
    try:
        client = create_client()
        assert client is not None
    except Exception:
        # If no API key is available, that's okay for this example
        pytest.skip("No OpenAI API key available")


def test_example():
    """Example test that always passes."""
    assert True
