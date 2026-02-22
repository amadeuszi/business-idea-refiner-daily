import logging

from agents.idea_refiner.generation.models import LABELS, MODELS

log = logging.getLogger(__name__)


def accept(verdict: dict, state: dict) -> None:
    state["winner_label"] = verdict["winner"]
    state["winning_idea"] = verdict.get("winning_idea") or state["ideas"][verdict["winner"]]
    state["all_evals"] = verdict.get("evaluations", [])
    state["winner_ev"] = next(
        (e for e in state["all_evals"] if e["idea_label"] == state["winner_label"]), None
    )
    log.info(
        "🏆 Winner: Idea %s (%s)",
        state["winner_label"],
        MODELS[LABELS.index(state["winner_label"])]["name"],
    )
