import logging

from agents.idea_refiner.config import MAX_RETRIES, get_idea_prompt
from agents.idea_refiner.output.display import display_and_save
from agents.idea_refiner.pipeline.state import init_state
from agents.idea_refiner.pipeline.run_round import run_round

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)


def main() -> str:
    theme, system_prompt, user_prompt = get_idea_prompt()
    state = init_state(theme)
    for rnd in range(1, MAX_RETRIES + 2):
        if run_round(rnd, state, system_prompt, user_prompt):
            break
    return display_and_save(theme, state)


if __name__ == "__main__":
    main()
