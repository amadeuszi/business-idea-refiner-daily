import logging

from agents.idea_refiner.config import MAX_RETRIES
from agents.idea_refiner.generation.models import LABELS, MODELS
from agents.idea_refiner.generation.prompt import build_feedback_message

log = logging.getLogger(__name__)


def prepare_retries(verdict: dict, state: dict) -> bool:
    """Set up feedback for next round. Returns True if no retries remain (done)."""
    log.info("🔄 All ideas rejected. Preparing retries...")
    fb = verdict.get("rejection_feedback", {})
    any_retry = False
    for label in LABELS:
        if fb.get(label) and state["attempts"][label] < MAX_RETRIES + 1:
            state["messages"][label].append(build_feedback_message(fb[label]))
            state["needs_gen"][label] = True
            any_retry = True
            log.info(
                "   [%s] %s — will retry. Feedback: %s",
                label,
                MODELS[LABELS.index(label)]["name"],
                str(fb[label])[:120] + ("..." if len(str(fb[label])) > 120 else ""),
            )
        else:
            state["needs_gen"][label] = False
            if state["attempts"][label] >= MAX_RETRIES + 1:
                log.info(
                    "   [%s] %s — max retries reached",
                    label,
                    MODELS[LABELS.index(label)]["name"],
                )
    if not any_retry:
        evals = verdict.get("evaluations", [])
        best = max(
            evals,
            key=lambda e: (
                e["acquisition_score"] + e["demand_score"] + e.get("build_score", 0)
            ),
        )
        state.update(
            {
                "winner_label": best["idea_label"],
                "winning_idea": state["ideas"][best["idea_label"]],
                "winner_ev": best,
                "all_evals": evals,
            }
        )
        log.info(
            "⚠️  No retries left. Fallback winner: Idea %s (%s)",
            best["idea_label"],
            MODELS[LABELS.index(best["idea_label"])]["name"],
        )
        return True
    return False
