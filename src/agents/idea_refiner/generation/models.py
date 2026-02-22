from agents.idea_refiner.generation.gpt52 import generate_gpt52
from agents.idea_refiner.generation.gemini import generate_gemini

LABELS = ["A", "B"]

MODELS = [
    {"name": "GPT-5.2 (OpenAI)", "generate": generate_gpt52},
    {"name": "Gemini 3.1 Pro", "generate": generate_gemini},
]


def get_model(label: str) -> dict:
    return MODELS[LABELS.index(label)]
