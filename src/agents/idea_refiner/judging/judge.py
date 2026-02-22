import json
import random

from agents.idea_refiner.generation.clients import get_client
from agents.idea_refiner.config import JUDGE_SYSTEM
from agents.idea_refiner.generation.models import LABELS


def _shuffle_ideas(ideas: dict) -> tuple[dict, str]:
    order = list(ideas.keys())
    random.shuffle(order)
    shuffle_map = {LABELS[i]: orig for i, orig in enumerate(order)}
    ideas_text = "".join(
        f"\n{'='*60}\nIdea {p}:\n{'='*60}\n{ideas[o]}\n"
        for p, o in shuffle_map.items()
    )
    return shuffle_map, ideas_text


def _call_judge(ideas_text: str) -> str:
    resp = get_client("gemini").chat.completions.create(
        model="gemini-3.1-pro-preview",
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": f"Evaluate these business ideas:\n{ideas_text}"},
        ],
    )
    return resp.choices[0].message.content


def _parse_raw(raw: str) -> dict:
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0]
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0]
    return json.loads(raw.strip())


def _remap(result: dict, shuffle_map: dict) -> dict:
    for ev in result.get("evaluations", []):
        ev["idea_label"] = shuffle_map.get(ev["idea_label"], ev["idea_label"])
    if result.get("winner"):
        result["winner"] = shuffle_map.get(result["winner"], result["winner"])
    result["rejection_feedback"] = {
        shuffle_map.get(k, k): v for k, v in result.get("rejection_feedback", {}).items()
    }
    return result


def judge_ideas(ideas: dict[str, str]) -> dict:
    shuffle_map, ideas_text = _shuffle_ideas(ideas)
    return _remap(_parse_raw(_call_judge(ideas_text)), shuffle_map)
