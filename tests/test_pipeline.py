from unittest.mock import patch

from agents.idea_refiner.pipeline.state import init_state
from agents.idea_refiner.pipeline.accept import accept
from agents.idea_refiner.pipeline.retry import prepare_retries
from agents.idea_refiner.pipeline.verdict import apply_verdict
from agents.idea_refiner.pipeline.generate_step import generate_needed
from agents.idea_refiner.pipeline.run_round import run_round
from agents.idea_refiner.config import MAX_RETRIES


class TestInitState:
    @patch("agents.idea_refiner.pipeline.state.get_client")
    def test_returns_all_required_keys(self, mock_get_client):
        state = init_state("cooking")
        required = {"attempts", "messages", "ideas", "needs_gen", "winner_label",
                     "winning_idea", "winner_ev", "all_evals", "start"}
        assert required.issubset(state.keys())

    @patch("agents.idea_refiner.pipeline.state.get_client")
    def test_initial_attempts_zero(self, mock_get_client):
        state = init_state(None)
        for label in ("A", "B"):
            assert state["attempts"][label] == 0

    @patch("agents.idea_refiner.pipeline.state.get_client")
    def test_all_need_generation(self, mock_get_client):
        state = init_state("fitness")
        assert all(state["needs_gen"].values())


class TestAccept:
    def test_accept_sets_winner(self, pipeline_state, fake_verdict_accept):
        pipeline_state["ideas"] = {"A": "idea A", "B": "idea B"}
        accept(fake_verdict_accept, pipeline_state)

        assert pipeline_state["winner_label"] == "A"
        assert pipeline_state["winning_idea"] is not None
        assert pipeline_state["winner_ev"] is not None
        assert pipeline_state["winner_ev"]["idea_label"] == "A"

    def test_accept_falls_back_to_state_idea_when_missing(self, pipeline_state):
        pipeline_state["ideas"] = {"A": "my raw idea", "B": "other"}
        verdict = {
            "evaluations": [
                {"idea_label": "A", "acquisition_score": 9, "demand_score": 9,
                 "build_score": 9, "explanation": "ok"},
            ],
            "verdict": "accept",
            "winner": "A",
            "winning_idea": None,
            "rejection_feedback": {},
        }
        accept(verdict, pipeline_state)
        assert pipeline_state["winning_idea"] == "my raw idea"


class TestPrepareRetries:
    def test_retries_set_needs_gen_and_append_feedback(self, populated_state, fake_verdict_reject):
        done = prepare_retries(fake_verdict_reject, populated_state)
        assert not done
        assert populated_state["needs_gen"]["A"] is True
        assert populated_state["needs_gen"]["B"] is True
        assert any("COMPLETELY DIFFERENT" in m["content"]
                    for m in populated_state["messages"]["A"] if m["role"] == "user")

    def test_max_retries_falls_back_to_best(self, populated_state, fake_verdict_reject):
        for label in ("A", "B"):
            populated_state["attempts"][label] = MAX_RETRIES + 1
        done = prepare_retries(fake_verdict_reject, populated_state)
        assert done
        assert populated_state["winner_label"] is not None
        assert populated_state["winning_idea"] is not None

    def test_partial_retry_one_at_max(self, populated_state, fake_verdict_reject):
        populated_state["attempts"]["A"] = MAX_RETRIES + 1
        populated_state["attempts"]["B"] = 1
        done = prepare_retries(fake_verdict_reject, populated_state)
        assert not done
        assert populated_state["needs_gen"]["A"] is False
        assert populated_state["needs_gen"]["B"] is True

    def test_fallback_picks_highest_total_score(self, populated_state):
        verdict = {
            "evaluations": [
                {"idea_label": "A", "acquisition_score": 5, "demand_score": 5,
                 "build_score": 5, "explanation": "ok"},
                {"idea_label": "B", "acquisition_score": 8, "demand_score": 7,
                 "build_score": 6, "explanation": "better"},
            ],
            "verdict": "reject_all",
            "winner": None,
            "winning_idea": None,
            "rejection_feedback": {"A": "fb", "B": "fb"},
        }
        for label in ("A", "B"):
            populated_state["attempts"][label] = MAX_RETRIES + 1
        done = prepare_retries(verdict, populated_state)
        assert done
        assert populated_state["winner_label"] == "B"


class TestApplyVerdict:
    def test_none_verdict_falls_back_to_A(self, populated_state):
        done = apply_verdict(None, populated_state)
        assert done
        assert populated_state["winner_label"] == "A"
        assert populated_state["winning_idea"] == populated_state["ideas"]["A"]

    def test_accept_verdict(self, populated_state, fake_verdict_accept):
        done = apply_verdict(fake_verdict_accept, populated_state)
        assert done
        assert populated_state["winner_label"] == "A"

    def test_reject_verdict_triggers_retries(self, populated_state, fake_verdict_reject):
        done = apply_verdict(fake_verdict_reject, populated_state)
        assert not done


class TestGenerateNeeded:
    @patch("agents.idea_refiner.pipeline.generate_step.generate_parallel")
    def test_generates_for_needed_labels(self, mock_parallel, pipeline_state):
        mock_parallel.return_value = [
            ("A", "idea A text", 1.0),
            ("B", "idea B text", 1.5),
        ]
        generate_needed(pipeline_state, "system prompt", "user prompt")

        assert pipeline_state["ideas"]["A"] == "idea A text"
        assert pipeline_state["ideas"]["B"] == "idea B text"
        assert pipeline_state["attempts"]["A"] == 1
        assert pipeline_state["attempts"]["B"] == 1

    @patch("agents.idea_refiner.pipeline.generate_step.generate_parallel")
    def test_skips_labels_not_needing_gen(self, mock_parallel, populated_state):
        generate_needed(populated_state, "sys", "usr")
        mock_parallel.assert_not_called()

    @patch("agents.idea_refiner.pipeline.generate_step.generate_parallel")
    def test_handles_generation_failure(self, mock_parallel, pipeline_state):
        mock_parallel.return_value = [("A", None, 1.0), ("B", "good idea", 0.5)]
        generate_needed(pipeline_state, "sys", "usr")
        assert "Error" in pipeline_state["ideas"]["A"]
        assert pipeline_state["ideas"]["B"] == "good idea"

    @patch("agents.idea_refiner.pipeline.generate_step.generate_parallel")
    def test_builds_initial_messages_on_first_gen(self, mock_parallel, pipeline_state):
        mock_parallel.return_value = [("A", "idea", 0.5)]
        pipeline_state["needs_gen"] = {"A": True, "B": False}
        generate_needed(pipeline_state, "system!", "user!")
        assert pipeline_state["messages"]["A"][0]["content"] == "system!"
        assert pipeline_state["messages"]["A"][1]["content"] == "user!"


class TestRunRound:
    @patch("agents.idea_refiner.pipeline.run_round.apply_verdict")
    @patch("agents.idea_refiner.pipeline.run_round.judge_and_log")
    @patch("agents.idea_refiner.pipeline.run_round.generate_needed")
    def test_calls_generate_judge_verdict(self, mock_gen, mock_judge, mock_verdict):
        mock_verdict.return_value = True
        mock_judge.return_value = {"verdict": "accept"}

        state = {"ideas": {}, "needs_gen": {"A": True, "B": True}}
        result = run_round(1, state, "sys", "usr")

        mock_gen.assert_called_once()
        mock_judge.assert_called_once_with(state)
        mock_verdict.assert_called_once()
        assert result is True
