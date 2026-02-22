import logging

from agents.idea_refiner.pipeline.generate_step import generate_needed
from agents.idea_refiner.pipeline.judge_step import judge_and_log
from agents.idea_refiner.pipeline.verdict import apply_verdict

log = logging.getLogger(__name__)


def run_round(round_num: int, state: dict, system_prompt: str, user_prompt: str) -> bool:
    log.info("\n%s\n📋 ROUND %d\n%s", "━" * 60, round_num, "━" * 60)
    generate_needed(state, system_prompt, user_prompt)
    return apply_verdict(judge_and_log(state), state)
