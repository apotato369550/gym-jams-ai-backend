import os
import json
from pathlib import Path
import httpx
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL")
MODEL = os.getenv("MODEL")
PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"


def load_prompt(name: str) -> str:
    """Load a prompt template from the prompts/ directory."""
    return (PROMPTS_DIR / f"{name}.txt").read_text()


async def call_llm(system_prompt: str, user_message: str) -> dict:
    """Call OpenRouter with a system prompt and user message. Returns parsed JSON or raw text."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            },
            timeout=60.0,
        )
    return response.json()
