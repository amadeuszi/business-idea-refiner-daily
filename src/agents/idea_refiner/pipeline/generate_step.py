import logging
import time

from agents.idea_refiner.config import MAX_RETRIES
from agents.idea_refiner.generation.models import LABELS, MODELS
from agents.idea_refiner.generation.prompt import build_initial_messages
from agents.idea_refiner.generation.runner import generate_parallel

log = logging.getLogger(__name__)


def generate_needed(state: dict, system_prompt: str, user_prompt: str) -> None:
    tasks = []
    for label, model in zip(LABELS, MODELS):
        if not state["needs_gen"][label]:
            log.info("   [%s] %s — keeping previous idea", label, model["name"])
            continue
        state["attempts"][label] += 1
        retry_note = " (with feedback)" if state["attempts"][label] > 1 else ""
        log.info(
            "   [%s] %s — queuing (attempt %d/%d)%s",
            label, model["name"],
            state["attempts"][label], MAX_RETRIES + 1,
            retry_note,
        )
        if not state["messages"][label]:
            state["messages"][label] = build_initial_messages(system_prompt, user_prompt)
        tasks.append((label, model, state["messages"][label]))
    if not tasks:
        return
    log.info("   ⏳ Generating %d idea(s) in parallel...", len(tasks))
    t0 = time.time()
    for label, idea, elapsed in generate_parallel(tasks):
        model_name = MODELS[LABELS.index(label)]["name"]
        if idea:
            state["ideas"][label] = idea
            state["messages"][label].append({"role": "assistant", "content": idea})
            log.info("   [%s] %s — ✅ (%.1fs)", label, model_name, elapsed)
        else:
            state["ideas"][label] = f"[Error: generation failed for {model_name}]"
            log.warning("   [%s] %s — ⚠️  failed", label, model_name)
    log.info("   ⏱️  All done in %.1fs", time.time() - t0)
