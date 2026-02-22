from unittest.mock import MagicMock


def make_chat_response(content: str) -> MagicMock:
    """Build a fake OpenAI chat completion response."""
    resp = MagicMock()
    resp.choices = [MagicMock()]
    resp.choices[0].message.content = content
    return resp
