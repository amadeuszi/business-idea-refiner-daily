import time

import pytest


@pytest.fixture()
def fake_verdict_accept():
    return {
        "evaluations": [
            {
                "idea_label": "A",
                "acquisition_score": 9,
                "demand_score": 9,
                "build_score": 9,
                "explanation": "Great idea with clear ad hook.",
            },
            {
                "idea_label": "B",
                "acquisition_score": 7,
                "demand_score": 8,
                "build_score": 8,
                "explanation": "Decent but harder to market.",
            },
        ],
        "verdict": "accept",
        "winner": "A",
        "winning_idea": "**Product Name:** WidgetMaster\n\n**One-Line Pitch:** Build widgets fast.",
        "rejection_feedback": {"A": None, "B": "Hard to acquire customers."},
    }


@pytest.fixture()
def fake_verdict_reject():
    return {
        "evaluations": [
            {
                "idea_label": "A",
                "acquisition_score": 6,
                "demand_score": 5,
                "build_score": 7,
                "explanation": "Too niche.",
            },
            {
                "idea_label": "B",
                "acquisition_score": 5,
                "demand_score": 6,
                "build_score": 6,
                "explanation": "Unclear value prop.",
            },
        ],
        "verdict": "reject_all",
        "winner": None,
        "winning_idea": None,
        "rejection_feedback": {
            "A": "Too niche, unclear ad hook.",
            "B": "Weak demand signal.",
        },
    }


@pytest.fixture()
def pipeline_state():
    return {
        "attempts": {"A": 0, "B": 0},
        "messages": {"A": [], "B": []},
        "ideas": {},
        "needs_gen": {"A": True, "B": True},
        "winner_label": None,
        "winning_idea": None,
        "winner_ev": None,
        "all_evals": [],
        "start": time.time(),
    }


@pytest.fixture()
def populated_state(pipeline_state):
    pipeline_state["ideas"] = {
        "A": "**Product Name:** IdeaA\n\n**One-Line Pitch:** A is great.",
        "B": "**Product Name:** IdeaB\n\n**One-Line Pitch:** B is great.",
    }
    pipeline_state["attempts"] = {"A": 1, "B": 1}
    pipeline_state["needs_gen"] = {"A": False, "B": False}
    pipeline_state["messages"] = {
        "A": [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "usr"},
            {"role": "assistant", "content": pipeline_state["ideas"]["A"]},
        ],
        "B": [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "usr"},
            {"role": "assistant", "content": pipeline_state["ideas"]["B"]},
        ],
    }
    return pipeline_state


