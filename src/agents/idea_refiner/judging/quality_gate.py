import logging

log = logging.getLogger(__name__)


def enforce_quality_gate(verdict: dict) -> dict:
    if verdict["verdict"] != "accept" or not verdict.get("winner"):
        return verdict
    evals = verdict.get("evaluations", [])
    w_ev = next((e for e in evals if e["idea_label"] == verdict["winner"]), None)
    if not w_ev:
        return verdict
    acq, dem, bld = (
        w_ev["acquisition_score"],
        w_ev["demand_score"],
        w_ev.get("build_score", 0),
    )
    if acq < 9 or dem < 9 or bld < 9:
        log.info(
            "⚠️  Overriding accept — scores (%d/%d/%d) below 9+ threshold",
            acq, dem, bld,
        )
        verdict.update({"verdict": "reject_all", "winner": None, "winning_idea": None})
        if not verdict.get("rejection_feedback"):
            verdict["rejection_feedback"] = {
                ev["idea_label"]: (
                    f"Scores {ev['acquisition_score']}/{ev['demand_score']}/"
                    f"{ev.get('build_score',0)}. {ev['explanation']}"
                )
                for ev in evals
            }
    return verdict
