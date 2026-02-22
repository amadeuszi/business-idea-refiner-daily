import logging
import time

from agents.idea_refiner.judging.judge import judge_ideas
from agents.idea_refiner.judging.quality_gate import enforce_quality_gate
from agents.idea_refiner.generation.models import LABELS, MODELS

log = logging.getLogger(__name__)


def judge_and_log(state: dict) -> dict | None:
    log.info("\n⚖️  Sending to judge (Gemini 3.1 Pro Preview)...")
    log.info("   Note: judge sees shuffled labels — no model names, no ordering bias")
    t0 = time.time()
    try:
        verdict = judge_ideas(state["ideas"])
    except Exception as e:
        log.error("❌ Judge failed after %.1fs: %s", time.time() - t0, e)
        return None
    log.info("   ⏱️  %.1fs | Verdict: %s", time.time() - t0, verdict["verdict"].upper())
    for ev in verdict.get("evaluations", []):
        log.info(
            "   [%s] %s — acq:%d dem:%d bld:%d — %s",
            ev["idea_label"],
            MODELS[LABELS.index(ev["idea_label"])]["name"],
            ev["acquisition_score"],
            ev["demand_score"],
            ev.get("build_score", 0),
            ev["explanation"],
        )
    return enforce_quality_gate(verdict)
