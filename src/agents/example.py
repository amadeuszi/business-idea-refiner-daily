"""Example module for AI agent interactions."""

import os
from typing import Optional

from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def create_client(api_key: Optional[str] = None) -> OpenAI:
    """
    Create an OpenAI client.
    
    Args:
        api_key: Optional API key. If not provided, uses OPENAI_API_KEY from environment.
    
    Returns:
        OpenAI client instance.
    """
    if api_key is None:
        api_key = os.getenv("OPENAI_API_KEY")
    
    return OpenAI(api_key=api_key)


def simple_completion(prompt: str, model: str = "gpt-4") -> str:
    """
    Generate a simple completion using OpenAI.
    
    Args:
        prompt: The prompt to send to the model.
        model: The model to use (default: gpt-4).
    
    Returns:
        The generated completion text.
    """
    client = create_client()
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content


if __name__ == "__main__":
    # Example usage
    result = simple_completion("Say hello!")
    print(result)
