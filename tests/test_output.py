from unittest.mock import AsyncMock, patch, MagicMock

from agents.idea_refiner.output.telegram import _md_to_html, _build_messages, send_telegram_summary


class TestMdToHtml:
    def test_bold_conversion(self):
        assert _md_to_html("**hello**") == "<b>hello</b>"

    def test_italic_conversion(self):
        assert _md_to_html("_world_") == "<i>world</i>"

    def test_bold_and_italic_together(self):
        result = _md_to_html("**bold** and _italic_")
        assert "<b>bold</b>" in result
        assert "<i>italic</i>" in result

    def test_no_conversion_for_plain_text(self):
        assert _md_to_html("plain text") == "plain text"

    def test_underscore_inside_word_not_converted(self):
        assert _md_to_html("snake_case_var") == "snake_case_var"


class TestBuildMessages:
    def _make_state(self, winning_idea="**Product Name:** TestProd"):
        return {
            "winner_label": "A",
            "winning_idea": winning_idea,
            "all_evals": [
                {"idea_label": "A", "acquisition_score": 9, "demand_score": 9,
                 "build_score": 9, "explanation": "Great idea."},
                {"idea_label": "B", "acquisition_score": 6, "demand_score": 7,
                 "build_score": 8, "explanation": "Okay idea."},
            ],
            "winner_ev": {"idea_label": "A", "explanation": "Great idea."},
        }

    def test_single_message_for_short_content(self):
        msgs = _build_messages("cooking", self._make_state(), 42.0, "2026-02-22")
        assert len(msgs) == 1
        assert "Daily Idea Run" in msgs[0]
        assert "cooking" in msgs[0]

    def test_contains_scoreboard(self):
        msgs = _build_messages(None, self._make_state(), 10.0, "2026-02-22")
        assert "Scoreboard" in msgs[0]

    def test_contains_winner_trophy(self):
        msgs = _build_messages(None, self._make_state(), 10.0, "2026-02-22")
        full = "".join(msgs)
        assert "🏆" in full

    def test_long_idea_splits_into_multiple_messages(self):
        long_idea = "x" * 5000
        msgs = _build_messages("theme", self._make_state(long_idea), 10.0, "2026-02-22")
        assert len(msgs) > 1

    def test_no_theme_shows_open(self):
        msgs = _build_messages(None, self._make_state(), 5.0, "2026-02-22")
        assert "Open (no theme)" in msgs[0]

    def test_html_formatting_applied(self):
        state = self._make_state("**Bold Product**")
        msgs = _build_messages("t", state, 5.0, "2026-02-22")
        full = "".join(msgs)
        assert "<b>Bold Product</b>" in full


class TestSendTelegram:
    def _make_state(self):
        return {
            "winner_label": "A",
            "winning_idea": "**Product Name:** TestProd",
            "all_evals": [
                {"idea_label": "A", "acquisition_score": 9, "demand_score": 9,
                 "build_score": 9, "explanation": "Great."},
            ],
            "winner_ev": {"idea_label": "A", "explanation": "Great."},
        }

    @patch("agents.idea_refiner.output.telegram.os.getenv", return_value=None)
    def test_skips_when_no_token(self, mock_getenv):
        send_telegram_summary("theme", {"winner_label": "A"}, 10.0, "2026-02-22")
        mock_getenv.assert_called()

    @patch("agents.idea_refiner.output.telegram.Bot")
    @patch("agents.idea_refiner.output.telegram.os.getenv", side_effect=["fake-token", "12345"])
    def test_sends_message_when_configured(self, mock_getenv, mock_bot_cls):
        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()
        mock_bot_cls.return_value = mock_bot

        send_telegram_summary("cooking", self._make_state(), 10.0, "2026-02-22")

        mock_bot_cls.assert_called_once_with(token="fake-token")
        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args.kwargs
        assert call_kwargs["chat_id"] == "12345"
        assert "Daily Idea Run" in call_kwargs["text"]

    @patch("agents.idea_refiner.output.telegram.Bot")
    @patch("agents.idea_refiner.output.telegram.os.getenv", side_effect=["fake-token", "12345"])
    def test_sends_multiple_messages_for_long_idea(self, mock_getenv, mock_bot_cls):
        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()
        mock_bot_cls.return_value = mock_bot

        state = self._make_state()
        state["winning_idea"] = "x" * 5000
        send_telegram_summary("theme", state, 5.0, "2026-02-22")

        assert mock_bot.send_message.call_count > 1

    @patch("agents.idea_refiner.output.telegram.Bot")
    @patch("agents.idea_refiner.output.telegram.os.getenv", side_effect=["fake-token", "12345"])
    def test_handles_send_failure_gracefully(self, mock_getenv, mock_bot_cls):
        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock(side_effect=RuntimeError("network error"))
        mock_bot_cls.return_value = mock_bot

        send_telegram_summary("theme", self._make_state(), 5.0, "2026-02-22")


class TestConsole:
    def test_print_results_does_not_crash(self, capsys):
        from agents.idea_refiner.output.console import print_results
        state = {
            "winner_label": "A",
            "winning_idea": "A great product idea.",
            "all_evals": [
                {"idea_label": "A", "acquisition_score": 9, "demand_score": 9,
                 "build_score": 9, "explanation": "Nice."},
                {"idea_label": "B", "acquisition_score": 7, "demand_score": 7,
                 "build_score": 7, "explanation": "Okay."},
            ],
            "winner_ev": {"idea_label": "A", "explanation": "Nice."},
        }
        print_results("cooking", state, 12.5, "2026-02-22")
        output = capsys.readouterr().out
        assert "DAILY BUSINESS IDEA" in output
        assert "GPT-5.2" in output
        assert "A great product idea." in output

    def test_print_results_no_evals(self, capsys):
        from agents.idea_refiner.output.console import print_results
        state = {
            "winner_label": "A",
            "winning_idea": "Fallback idea.",
            "all_evals": [],
            "winner_ev": None,
        }
        print_results(None, state, 5.0, "2026-02-22")
        output = capsys.readouterr().out
        assert "Fallback idea." in output
