from unittest.mock import MagicMock, patch

from agents.idea_refiner.generation.prompt import build_feedback_message, build_initial_messages
from agents.idea_refiner.generation.models import LABELS, MODELS, get_model
from agents.idea_refiner.generation.gpt52 import generate_gpt52
from agents.idea_refiner.generation.gemini import generate_gemini
from agents.idea_refiner.generation.runner import generate_parallel

from tests.helpers import make_chat_response


class TestPrompt:
    def test_build_initial_messages(self):
        msgs = build_initial_messages("system prompt", "user prompt")
        assert len(msgs) == 2
        assert msgs[0] == {"role": "system", "content": "system prompt"}
        assert msgs[1] == {"role": "user", "content": "user prompt"}

    def test_build_feedback_message(self):
        msg = build_feedback_message("bad ad hook")
        assert msg["role"] == "user"
        assert "bad ad hook" in msg["content"]
        assert "COMPLETELY DIFFERENT" in msg["content"]


class TestModels:
    def test_labels_match_models_count(self):
        assert len(LABELS) == len(MODELS)

    def test_get_model_valid(self):
        for label in LABELS:
            model = get_model(label)
            assert "name" in model
            assert "generate" in model
            assert callable(model["generate"])

    def test_get_model_invalid_raises(self):
        try:
            get_model("Z")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass


class TestGPT52:
    @patch("agents.idea_refiner.generation.gpt52.get_client")
    def test_generate_gpt52_calls_openai(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = make_chat_response("idea text")
        mock_get_client.return_value = mock_client

        result = generate_gpt52([{"role": "user", "content": "hello"}])

        assert result == "idea text"
        mock_get_client.assert_called_once_with("openai")
        call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs.kwargs["model"] == "gpt-5.2"

    @patch("agents.idea_refiner.generation.gpt52.get_client")
    def test_generate_gpt52_passes_messages(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = make_chat_response("ok")
        mock_get_client.return_value = mock_client

        messages = [{"role": "system", "content": "sys"}, {"role": "user", "content": "usr"}]
        generate_gpt52(messages)

        call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs.kwargs["messages"] == messages


class TestGemini:
    @patch("agents.idea_refiner.generation.gemini.get_client")
    def test_generate_gemini_calls_gemini_client(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = make_chat_response("gemini idea")
        mock_get_client.return_value = mock_client

        result = generate_gemini([{"role": "user", "content": "hello"}])

        assert result == "gemini idea"
        mock_get_client.assert_called_once_with("gemini")
        call_kwargs = mock_client.chat.completions.create.call_args
        assert "gemini" in call_kwargs.kwargs["model"].lower()


class TestRunner:
    def test_generate_parallel_success(self):
        model_a = {"name": "ModelA", "generate": lambda msgs: "idea A"}
        model_b = {"name": "ModelB", "generate": lambda msgs: "idea B"}

        tasks = [
            ("A", model_a, [{"role": "user", "content": "go"}]),
            ("B", model_b, [{"role": "user", "content": "go"}]),
        ]
        results = generate_parallel(tasks)

        labels = {r[0] for r in results}
        assert labels == {"A", "B"}
        for label, idea, elapsed in results:
            assert idea is not None
            assert elapsed >= 0

    def test_generate_parallel_handles_error(self):
        def failing_gen(msgs):
            raise RuntimeError("API down")

        model = {"name": "BadModel", "generate": failing_gen}
        results = generate_parallel([("A", model, [])])

        assert len(results) == 1
        label, idea, elapsed = results[0]
        assert label == "A"
        assert idea is None

    def test_generate_parallel_empty_tasks(self):
        results = generate_parallel([])
        assert results == []
