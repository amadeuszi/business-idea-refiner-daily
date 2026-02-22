import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

_clients: dict = {}


def _openai_client() -> OpenAI:
    return OpenAI()


def _gemini_client() -> OpenAI:
    return OpenAI(
        api_key=os.getenv("GOOGLE_API_KEY"),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )


_factories = {"openai": _openai_client, "gemini": _gemini_client}


def get_client(name: str) -> OpenAI:
    if name not in _clients:
        _clients[name] = _factories[name]()
    return _clients[name]
