from unittest.mock import patch

from agents.idea_refiner.config import (
    IDEA_SYSTEM_PROMPT,
    IDEA_USER_TEMPLATE,
    MAX_RETRIES,
    RANDOM_THEMES,
    get_idea_prompt,
)


def test_random_themes_not_empty():
    assert len(RANDOM_THEMES) > 50


def test_max_retries_is_positive():
    assert MAX_RETRIES >= 1


def test_system_prompt_contains_required_sections():
    for section in ("Product Name", "One-Line Pitch", "Pricing", "Ad Strategy", "Path to $100"):
        assert section in IDEA_SYSTEM_PROMPT


def test_user_template_has_theme_placeholder():
    assert "{theme_section}" in IDEA_USER_TEMPLATE


class TestGetIdeaPrompt:
    def test_returns_three_elements(self):
        theme, system, user = get_idea_prompt()
        assert isinstance(system, str)
        assert isinstance(user, str)

    @patch("agents.idea_refiner.config.datetime")
    def test_even_day_picks_theme(self, mock_dt):
        mock_dt.now.return_value.timetuple.return_value.tm_yday = 100  # even
        theme, _, user = get_idea_prompt()
        assert theme is not None
        assert theme in RANDOM_THEMES
        assert "TODAY'S FOCUS" in user

    @patch("agents.idea_refiner.config.datetime")
    def test_odd_day_no_theme(self, mock_dt):
        mock_dt.now.return_value.timetuple.return_value.tm_yday = 101  # odd
        theme, _, user = get_idea_prompt()
        assert theme is None
        assert "TODAY'S FOCUS" not in user
