_FEEDBACK_TEMPLATE = (
    "Your idea was rejected by the judge. Here is the feedback:\n\n"
    "{feedback}\n\n"
    "Please generate a COMPLETELY DIFFERENT and BETTER idea that addresses this feedback. "
    "Do not repeat or slightly modify your previous idea — come up with something genuinely new. "
    "Focus especially on making the idea easy to acquire customers for "
    "and ensuring there is real market demand."
)


def build_initial_messages(system_prompt: str, user_prompt: str) -> list[dict]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def build_feedback_message(feedback: str) -> dict:
    return {"role": "user", "content": _FEEDBACK_TEMPLATE.format(feedback=feedback)}
