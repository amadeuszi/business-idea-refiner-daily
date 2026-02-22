"""Cloud Run Function entry point for the Idea Refiner pipeline."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import logging
import time

import functions_framework
from flask import Request, jsonify

from agents.idea_refiner.config import MAX_RETRIES, get_idea_prompt
from agents.idea_refiner.output.display import display_and_save
from agents.idea_refiner.pipeline.run_round import run_round
from agents.idea_refiner.pipeline.state import init_state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)


@functions_framework.http
def idea_refiner(request: Request):
    """HTTP handler that runs the idea generation pipeline.

    Returns JSON with the winning idea, evaluations, and timing.
    """
    start = time.time()
    theme, system_prompt, user_prompt = get_idea_prompt()
    state = init_state(theme)

    for rnd in range(1, MAX_RETRIES + 2):
        if run_round(rnd, state, system_prompt, user_prompt):
            break

    winning_idea = display_and_save(theme, state)

    return jsonify({
        "theme": theme,
        "winning_idea": winning_idea,
        "winner_label": state["winner_label"],
        "evaluations": state.get("all_evals", []),
        "elapsed_seconds": round(time.time() - start, 1),
    })
