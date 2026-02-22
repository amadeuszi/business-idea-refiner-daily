from agents.idea_refiner.pipeline.accept import accept
from agents.idea_refiner.pipeline.retry import prepare_retries


def apply_verdict(verdict: dict | None, state: dict) -> bool:
    """Returns True if processing is done."""
    if verdict is None:
        state["winner_label"] = "A"
        state["winning_idea"] = state["ideas"].get("A", "")
        return True
    if verdict["verdict"] == "accept" and verdict.get("winner"):
        accept(verdict, state)
        return True
    return prepare_retries(verdict, state)
