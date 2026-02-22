from agents.idea_refiner.generation.clients import get_client


def generate_gpt52(messages: list[dict]) -> str:
    resp = get_client("openai").chat.completions.create(
        model="gpt-5.2", messages=messages, reasoning_effort="high",
    )
    return resp.choices[0].message.content
