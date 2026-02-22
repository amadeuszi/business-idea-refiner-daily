import logging
import time

from agents.idea_refiner.generation.clients import get_client
from agents.idea_refiner.config import MAX_RETRIES
from agents.idea_refiner.generation.models import LABELS, MODELS

log = logging.getLogger(__name__)


def init_state(theme: str | None) -> dict:
    log.info("🚀 Starting Daily Business Idea Generator (Multi-Model)")
    log.info("   Models: %s", ", ".join(m["name"] for m in MODELS))
    log.info("   Judge: Gemini 3.1 Pro Preview | Theme: %s", theme or "OPEN (no theme)")
    log.info("   Max retries: %d | Initializing clients...", MAX_RETRIES)
    for name in ("openai", "gemini"):
        get_client(name)
    log.info("   ✅ All clients ready")
    return {
        "attempts": {label: 0 for label in LABELS},
        "messages": {label: [] for label in LABELS},
        "ideas": {},
        "needs_gen": {label: True for label in LABELS},
        "winner_label": None,
        "winning_idea": None,
        "winner_ev": None,
        "all_evals": [],
        "start": time.time(),
    }
