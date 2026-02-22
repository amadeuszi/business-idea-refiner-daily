import json
from unittest.mock import patch, MagicMock

from agents.idea_refiner.main import main

from tests.helpers import make_chat_response


FAKE_IDEA_A = """\
**Product Name:** QuickMenu

**One-Line Pitch:** Create a stunning digital menu for your restaurant in 60 seconds.

**Target Customer:** Small restaurant owners who want a modern online menu.

**The Problem:** Updating paper menus is expensive and slow.

**How It Works:** Upload your menu items, pick a template, share the link.

**Pricing:** $4.99/month

**Ad Strategy:** Facebook ads targeting restaurant owners, before/after carousel.

**Path to $100/month:** 20 customers x $4.99 = ~$100/month

**Week 1 Build:** Menu builder, templates, shareable link.

**Week 2 Build:** QR code generator, analytics, Stripe integration.

**Why This Is Fun:** Instant visual results, happy restaurant owners."""

FAKE_IDEA_B = """\
**Product Name:** PetReminder

**One-Line Pitch:** Never miss a vet appointment or medication again.

**Target Customer:** Pet owners who juggle multiple pets and appointments.

**The Problem:** Forgetting pet care schedules.

**How It Works:** Add your pets, set reminders, get push notifications.

**Pricing:** $1.99/month

**Ad Strategy:** Instagram ads with cute pet photos.

**Path to $100/month:** 50 customers x $1.99 = ~$100/month

**Week 1 Build:** Pet profiles, reminder system.

**Week 2 Build:** Push notifications, calendar sync.

**Why This Is Fun:** Pets!"""

FAKE_JUDGE_RESPONSE = json.dumps({
    "evaluations": [
        {
            "idea_label": "A",
            "acquisition_score": 9,
            "demand_score": 9,
            "build_score": 10,
            "explanation": "Restaurant owners are easy to target on Facebook. Clear pain point.",
        },
        {
            "idea_label": "B",
            "acquisition_score": 7,
            "demand_score": 6,
            "build_score": 9,
            "explanation": "Niche audience, hard to convert via ads.",
        },
    ],
    "verdict": "accept",
    "winner": "A",
    "winning_idea": FAKE_IDEA_A,
    "rejection_feedback": {"A": None, "B": "Niche, weak demand."},
})


class TestMainIntegration:
    @patch("agents.idea_refiner.output.display.send_telegram_summary")
    @patch("agents.idea_refiner.pipeline.state.get_client")
    @patch("agents.idea_refiner.judging.judge.get_client")
    @patch("agents.idea_refiner.generation.gemini.get_client")
    @patch("agents.idea_refiner.generation.gpt52.get_client")
    def test_main_accepts_on_first_round(
        self, mock_gpt_client, mock_gem_client, mock_judge_client,
        mock_state_client, mock_telegram,
    ):
        gpt_client = MagicMock()
        gpt_client.chat.completions.create.return_value = make_chat_response(FAKE_IDEA_A)
        mock_gpt_client.return_value = gpt_client

        gem_client = MagicMock()
        gem_client.chat.completions.create.return_value = make_chat_response(FAKE_IDEA_B)
        mock_gem_client.return_value = gem_client

        judge_client = MagicMock()
        judge_client.chat.completions.create.return_value = make_chat_response(
            FAKE_JUDGE_RESPONSE
        )
        mock_judge_client.return_value = judge_client

        result = main()

        assert "QuickMenu" in result
        assert gpt_client.chat.completions.create.call_count == 1
        assert gem_client.chat.completions.create.call_count == 1
        assert judge_client.chat.completions.create.call_count == 1

    @patch("agents.idea_refiner.output.display.send_telegram_summary")
    @patch("agents.idea_refiner.pipeline.state.get_client")
    @patch("agents.idea_refiner.judging.judge.get_client")
    @patch("agents.idea_refiner.generation.gemini.get_client")
    @patch("agents.idea_refiner.generation.gpt52.get_client")
    def test_main_retries_then_accepts(
        self, mock_gpt_client, mock_gem_client, mock_judge_client,
        mock_state_client, mock_telegram,
    ):
        gpt_client = MagicMock()
        gpt_client.chat.completions.create.return_value = make_chat_response(FAKE_IDEA_A)
        mock_gpt_client.return_value = gpt_client

        gem_client = MagicMock()
        gem_client.chat.completions.create.return_value = make_chat_response(FAKE_IDEA_B)
        mock_gem_client.return_value = gem_client

        reject_response = json.dumps({
            "evaluations": [
                {"idea_label": "A", "acquisition_score": 5, "demand_score": 5,
                 "build_score": 5, "explanation": "Weak."},
                {"idea_label": "B", "acquisition_score": 4, "demand_score": 4,
                 "build_score": 4, "explanation": "Bad."},
            ],
            "verdict": "reject_all",
            "winner": None,
            "winning_idea": None,
            "rejection_feedback": {"A": "Try harder.", "B": "Much harder."},
        })

        judge_client = MagicMock()
        judge_client.chat.completions.create.side_effect = [
            make_chat_response(reject_response),
            make_chat_response(FAKE_JUDGE_RESPONSE),
        ]
        mock_judge_client.return_value = judge_client

        result = main()

        assert result is not None
        assert judge_client.chat.completions.create.call_count == 2
