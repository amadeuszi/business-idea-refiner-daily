import json
from unittest.mock import patch, MagicMock

from agents.idea_refiner.judging.judge import _parse_raw, _remap, _shuffle_ideas, judge_ideas
from agents.idea_refiner.judging.quality_gate import enforce_quality_gate

from tests.helpers import make_chat_response


class TestShuffleIdeas:
    def test_produces_all_labels(self):
        ideas = {"A": "idea A text", "B": "idea B text"}
        shuffle_map, ideas_text = _shuffle_ideas(ideas)
        assert set(shuffle_map.keys()) == {"A", "B"}
        assert set(shuffle_map.values()) == {"A", "B"}

    def test_ideas_text_contains_all_ideas(self):
        ideas = {"A": "unique-alpha-text", "B": "unique-beta-text"}
        _, ideas_text = _shuffle_ideas(ideas)
        assert "unique-alpha-text" in ideas_text
        assert "unique-beta-text" in ideas_text

    def test_ideas_text_contains_labels(self):
        ideas = {"A": "x", "B": "y"}
        _, ideas_text = _shuffle_ideas(ideas)
        assert "Idea A" in ideas_text
        assert "Idea B" in ideas_text


class TestParseRaw:
    def test_parse_plain_json(self):
        raw = '{"verdict": "accept", "winner": "A"}'
        result = _parse_raw(raw)
        assert result["verdict"] == "accept"

    def test_parse_json_in_code_fence(self):
        raw = '```json\n{"verdict": "reject_all"}\n```'
        result = _parse_raw(raw)
        assert result["verdict"] == "reject_all"

    def test_parse_json_in_plain_code_fence(self):
        raw = '```\n{"winner": "B"}\n```'
        result = _parse_raw(raw)
        assert result["winner"] == "B"

    def test_parse_invalid_json_raises(self):
        try:
            _parse_raw("not json at all")
            assert False, "Should have raised"
        except (json.JSONDecodeError, ValueError):
            pass


class TestRemap:
    def test_remap_swaps_labels(self):
        result = {
            "evaluations": [
                {"idea_label": "A", "acquisition_score": 9, "demand_score": 9, "build_score": 9,
                 "explanation": "ok"},
                {"idea_label": "B", "acquisition_score": 7, "demand_score": 7, "build_score": 7,
                 "explanation": "ok"},
            ],
            "verdict": "accept",
            "winner": "A",
            "rejection_feedback": {"A": None, "B": "meh"},
        }
        # A -> B, B -> A (the judge saw them shuffled)
        shuffle_map = {"A": "B", "B": "A"}
        remapped = _remap(result, shuffle_map)

        assert remapped["winner"] == "B"
        labels = [e["idea_label"] for e in remapped["evaluations"]]
        assert set(labels) == {"A", "B"}
        assert "A" in remapped["rejection_feedback"]

    def test_remap_identity(self):
        result = {
            "evaluations": [{"idea_label": "A", "explanation": "x"}],
            "verdict": "reject_all",
            "winner": None,
            "rejection_feedback": {"A": "fb"},
        }
        shuffle_map = {"A": "A", "B": "B"}
        remapped = _remap(result, shuffle_map)
        assert remapped["evaluations"][0]["idea_label"] == "A"


class TestJudgeIdeas:
    @patch("agents.idea_refiner.judging.judge.get_client")
    def test_judge_ideas_end_to_end(self, mock_get_client):
        judge_response = json.dumps({
            "evaluations": [
                {"idea_label": "A", "acquisition_score": 9, "demand_score": 9,
                 "build_score": 9, "explanation": "Excellent."},
                {"idea_label": "B", "acquisition_score": 6, "demand_score": 5,
                 "build_score": 7, "explanation": "Weak."},
            ],
            "verdict": "accept",
            "winner": "A",
            "winning_idea": "The great idea.",
            "rejection_feedback": {"A": None, "B": "Not good enough."},
        })
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = make_chat_response(judge_response)
        mock_get_client.return_value = mock_client

        ideas = {"A": "Idea Alpha", "B": "Idea Beta"}
        result = judge_ideas(ideas)

        assert result["verdict"] == "accept"
        assert result["winner"] in ("A", "B")
        assert len(result["evaluations"]) == 2


class TestQualityGate:
    def test_accept_with_high_scores_passes(self, fake_verdict_accept):
        result = enforce_quality_gate(fake_verdict_accept)
        assert result["verdict"] == "accept"
        assert result["winner"] == "A"

    def test_accept_with_low_scores_overridden_to_reject(self):
        verdict = {
            "evaluations": [
                {"idea_label": "A", "acquisition_score": 8, "demand_score": 9,
                 "build_score": 9, "explanation": "Almost."},
            ],
            "verdict": "accept",
            "winner": "A",
            "winning_idea": "Some idea",
            "rejection_feedback": {},
        }
        result = enforce_quality_gate(verdict)
        assert result["verdict"] == "reject_all"
        assert result["winner"] is None
        assert result["winning_idea"] is None

    def test_reject_verdict_passes_through(self, fake_verdict_reject):
        result = enforce_quality_gate(fake_verdict_reject)
        assert result["verdict"] == "reject_all"

    def test_accept_missing_winner_eval_passes_through(self):
        verdict = {
            "evaluations": [],
            "verdict": "accept",
            "winner": "A",
            "winning_idea": "idea",
        }
        result = enforce_quality_gate(verdict)
        assert result["verdict"] == "accept"

    def test_all_scores_exactly_nine_passes(self):
        verdict = {
            "evaluations": [
                {"idea_label": "B", "acquisition_score": 9, "demand_score": 9,
                 "build_score": 9, "explanation": "Perfect."},
            ],
            "verdict": "accept",
            "winner": "B",
            "winning_idea": "Perfect idea",
            "rejection_feedback": {},
        }
        result = enforce_quality_gate(verdict)
        assert result["verdict"] == "accept"

    def test_generates_feedback_when_overriding(self):
        verdict = {
            "evaluations": [
                {"idea_label": "A", "acquisition_score": 7, "demand_score": 8,
                 "build_score": 6, "explanation": "Meh."},
            ],
            "verdict": "accept",
            "winner": "A",
            "winning_idea": "idea",
            "rejection_feedback": {},
        }
        result = enforce_quality_gate(verdict)
        assert result["verdict"] == "reject_all"
        assert "A" in result["rejection_feedback"]
        assert "7/8/6" in result["rejection_feedback"]["A"]
