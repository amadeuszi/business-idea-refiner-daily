import logging
import time
from datetime import datetime

from agents.idea_refiner.output.console import print_results
from agents.idea_refiner.output.telegram import send_telegram_summary

log = logging.getLogger(__name__)


def display_and_save(theme: str | None, state: dict) -> str:
    if not state["winner_label"]:
        state["winner_label"] = "A"
        state["winning_idea"] = state["ideas"].get("A", "No idea generated")
    total_elapsed = time.time() - state["start"]
    today = datetime.now().strftime("%Y-%m-%d")
    log.info("⏱️  Total time: %.1fs", total_elapsed)
    print_results(theme, state, total_elapsed, today)
    send_telegram_summary(theme, state, total_elapsed, today)
    return state["winning_idea"]
