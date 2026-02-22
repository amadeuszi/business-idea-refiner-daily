from agents.idea_refiner.generation.clients import get_client


def generate_gemini(messages: list[dict]) -> str:
    resp = get_client("gemini").chat.completions.create(
        model="gemini-3.1-pro-preview", messages=messages, reasoning_effort="high",
    )
    return resp.choices[0].message.content
